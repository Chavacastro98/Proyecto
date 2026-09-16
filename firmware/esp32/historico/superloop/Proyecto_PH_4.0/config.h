#ifndef CONFIG_H
#define CONFIG_H

/**
 * =================================================================================
 * CONFIGURACIÓN GLOBAL DEL SISTEMA (config.h) — Versión 4.0
 * =================================================================================
 * Este archivo centraliza todo lo que los demás archivos del proyecto necesitan
 * compartir: las librerías comunes, las constantes de pines del circuito, y la
 * lista de variables globales que se usan desde varios lugares del programa.
 *
 * CAMBIOS v4.0:
 * - Arquitectura Modular MVC para el Servidor Web (Vistas en views/ y Controladores en controllers/)
 * - Desacoplamiento total de la capa de presentación respecto a la lógica de control
 * - Mantenimiento de todas las características de v3.5 (Lazo cerrado VCSS, ZCS +12V, OTA, pH 2.0)
 *
 * CAMBIOS v3.5:
 * - Lazo cerrado de corriente VCSS con sensado en shunts (ADS1115 Canales A2/A3)
 * - Pin de relé de aislamiento galvánico +12V (PIN_RELE_VCSS = GPIO 20) con protocolo ZCS
 * - Rutina de auto-calibración de transconductancia (Gm) persistida en Flash NVS
 *
 * CAMBIOS v3.0:
 * - Soporte para actualización OTA (Over-The-Air) via web upload
 * - Constante FIRMWARE_VERSION definida en Modulo_OTA.h
 * - Include de <Update.h> para la API de escritura en partición OTA
 *
 * CAMBIOS v2.0:
 * - Módulo de pH bajo demanda (On/Off) con variable phModuloActivo
 * - Soporte para 3 modos de calibración (Teórico, 2 Puntos, 3 Puntos)
 * - Variables de pendientes duales (ácida/básica) para calibración 3 puntos
 * - Voltaje crudo para calibración de hardware (offset de placa)
 * - Mutex dedicado muxPH para protección de variables del módulo pH
 *
 * MAPA DE CONEXIONES DEL ESP32 (PINES FÍSICOS DEL CIRCUITO):
 * ---------------------------------------------------------------------------------
 * PERIFÉRICO          | PIN ESP32 | FUNCIÓN
 * ---------------------------------------------------------------------------------
 * I2C (SDA)           | GPIO 8    | Datos I2C (ADS1115, MCP4725, AHT20, BMP280)
 * I2C (SCL)           | GPIO 9    | Reloj I2C (400 kHz)
 * SPI SCK Termopares  | GPIO 18   | Reloj SPI compartido para 4 sensores MAX6675
 * SPI SO Termopares   | GPIO 19   | Datos SPI compartido para 4 sensores MAX6675
 * CS Termopar 0       | GPIO 5    | Selector sensor Tina Limpieza
 * CS Termopar 1       | GPIO 4    | Selector sensor Tina Decapado
 * CS Termopar 2       | GPIO 13   | Selector sensor Tina Celda Hull
 * CS Termopar 3       | GPIO 14   | Selector sensor Tina Niquelado
 * UART2 (TX)          | GPIO 17   | Envío serie al Arduino Nano (9600 baud)
 * Relé VCSS (ZCS)     | GPIO 20   | Aislamiento físico de línea +12V (VDD Celda)
 * ---------------------------------------------------------------------------------
 *
 * REQUISITO DE COMPILACIÓN v4.0:
 * ---------------------------------------------------------------------------------
 * Para habilitar OTA, seleccionar en Arduino IDE:
 *   Tools → Partition Scheme → "Minimal SPIFFS (1.9MB APP with OTA/190KB SPIFFS)"
 * Esto crea dos particiones de aplicación de ~1.9MB cada una (esquema A/B).
 * ---------------------------------------------------------------------------------
 */

#include <Adafruit_ADS1X15.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include <Adafruit_MCP4725.h>
#include <Arduino.h>
#include <Preferences.h>
#include <WebServer.h>
#include <WiFi.h>
#include <Wire.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

// =================================================================================
// OBJETOS GLOBALES DE RED Y ALMACENAMIENTO (creados en Proyecto_PH_4.0.ino)
// =================================================================================
extern const char *ssid;     // Nombre de la red Wi-Fi que crea el ESP32
extern const char *password; // Contraseña de la red Wi-Fi
extern WebServer server;     // Servidor web para la interfaz de control (puerto 80)
extern Preferences memoria;  // Almacenamiento en memoria Flash para guardar configuraciones

// =================================================================================
// CONSTANTES DE PINES Y HARDWARE
// =================================================================================

// Voltaje de referencia del circuito impreso (3.3V)
#define VREF 3.3

// Pines SPI compartidos por los 4 amplificadores de termopar MAX6675
#define COMMON_SCK 18 // Reloj SPI (GPIO 18)
#define COMMON_SO 19  // Datos SPI (GPIO 19)

// =================================================================================
// CONSTANTES DEL MÓDULO PH 2.0
// =================================================================================

/**
 * Voltaje de offset teórico del módulo PH-4502C tras el divisor resistivo.
 * Con BNC en cortocircuito (0 mV de la sonda), el opamp entrega VCC/2 = 2.50V.
 * Después del divisor a 3.3V: 2.50 × (3.3/5.0) ≈ 1.650V en el ADS1115.
 */
#define PH_OFFSET_TEORICO 1.650f

/**
 * Pendiente teórica del sistema PH-4502C + divisor, expresada en pH/Voltio.
 * Se deriva del factor de Nernst (59.16 mV/pH @ 25°C) amplificado por la
 * ganancia del módulo (~5.7×) y atenuado por el divisor (×0.66):
 * Efectivo ≈ 235.7 mV/pH → 1/0.2357 ≈ 4.242 pH/V
 */
#define PH_PENDIENTE_TEORICA 4.242f

// =================================================================================
// SENSORES Y CONVERTIDORES EN EL BUS I2C (creados en sus respectivos módulos)
// =================================================================================
extern Adafruit_AHTX0   aht; // Sensor de temperatura y humedad (dirección I2C 0x38)
extern Adafruit_BMP280  bmp; // Sensor de presión atmosférica (dirección I2C 0x76 o 0x77)
extern Adafruit_ADS1115 ads; // Convertidor analógico-digital de 16 bits para sondas pH (0x48)
extern Adafruit_MCP4725 dac; // Convertidor digital-analógico de 12 bits para corriente (0x60)

// =================================================================================
// VARIABLES GLOBALES COMPARTIDAS
// =================================================================================

// --- Monitoreo Ambiental (se actualizan cada 5 segundos) ---
extern volatile float amb_temp; // Temperatura ambiente en °C (sensor AHT20)
extern volatile float amb_hum;  // Humedad relativa en % (sensor AHT20)
extern volatile float amb_pres; // Presión atmosférica en hPa (sensor BMP280)

// =================================================================================
// MÓDULO DE pH DUAL 2.0 — Variables Globales
// =================================================================================

// --- Control On/Off del Módulo ---
extern volatile bool phModuloActivo; // true = muestreo activo, false = standby (NO toca I2C)

// --- Selector de Modo de Calibración por Tina ---
// 0 = Teórico (Nernst, zero-config)
// 1 = 2 Puntos (lineal: pH 7 + pH 4)
// 2 = 3 Puntos (dual-slope: pH 4, 7 y 10)
extern volatile uint8_t tipoCalPH1; // Modo activo para Tina 1 (Zincado)
extern volatile uint8_t tipoCalPH2; // Modo activo para Tina 2 (Niquelado)

// --- Tina 1 (Zincado): Canal 0 del ADS1115 ---
extern volatile float v7_1;      // Voltaje medido al sumergir en solución pH 7.0
extern volatile float v4_1;      // Voltaje medido al sumergir en solución pH 4.0
extern volatile float v10_1;     // Voltaje medido al sumergir en solución pH 10.0 (3 puntos)
extern volatile float m_ph1;     // Pendiente lineal de calibración 2 puntos (pH/Voltio)
extern volatile float mAcida1;   // Pendiente ácida para 3 puntos: (4-7)/(V4-V7) [pH/V]
extern volatile float mBasica1;  // Pendiente básica para 3 puntos: (10-7)/(V10-V7) [pH/V]
extern volatile float phActual1; // Lectura de pH en tiempo real
extern volatile bool  calibradoPH1; // true si se completó la calibración del modo seleccionado

// --- Tina 2 (Niquelado): Canal 1 del ADS1115 ---
extern volatile float v7_2;
extern volatile float v4_2;
extern volatile float v10_2;
extern volatile float m_ph2;
extern volatile float mAcida2;
extern volatile float mBasica2;
extern volatile float phActual2;
extern volatile bool  calibradoPH2;

// --- Voltaje Crudo para Calibración de Hardware (Offset de Placa) ---
extern volatile float voltajeCrudoPH; // Último voltaje leído en crudo del canal 0 (3 decimales)

// --- Mutex de Protección del Módulo pH (separado del térmico) ---
extern portMUX_TYPE muxPH;

// --- Mutex de Protección de la Fuente de Corriente ---
extern portMUX_TYPE muxFuente;

// --- Fuente de Corriente (DAC MCP4725) ---
extern volatile bool fuenteActiva;         // true = salida de corriente encendida
extern volatile bool modoPulsado;          // true = corriente pulsada, false = corriente continua
extern volatile int  amplitudDAC;          // Valor digital efectivo enviado al DAC (0-4095)
extern volatile int  amplitudDAC_Setpoint; // Consigna digital deseada antes de compensación
extern volatile int  frecuencia;           // Frecuencia de pulso en Hz (1-100 Hz)
extern volatile int  dutyCycle;            // Porcentaje del tiempo en nivel alto (0-100 %)

// --- Sensado de Corriente VCSS y Compensación de Lazo Cerrado (v3.5) ---
#define PIN_RELE_VCSS 20      // Pin GPIO para el relé de aislamiento galvánico de +12V
#define RELE_NIVEL_ACTIVO LOW // Nivel lógico para energizar relé (Módulo Optoacoplado Active Low)

extern volatile bool  estadoReleVDD;          // true = relé cerrado (+12V activo), false = abierto (aislado)
extern volatile float corrienteReal_R1;        // Corriente calculada Rama 1 (Amperios)
extern volatile float corrienteReal_R2;        // Corriente calculada Rama 2 (Amperios)
extern volatile float corrienteTotalReal;      // Corriente total real I1 + I2 (Amperios)
extern volatile float voltajeShunt1_raw;       // Caída de tensión medida en Shunt 1 (Voltios)
extern volatile float voltajeShunt2_raw;       // Caída de tensión medida en Shunt 2 (Voltios)
extern volatile float factorGananciaVCSS;       // Factor de transconductancia calibrado (nominal = 1.000)
extern volatile bool  compensacionLazoCerrado; // true = corrección digital outer loop activa
extern unsigned long  lastSensadoVCSS;         // Temporizador de muestreo VCSS (cada 500 ms)

// --- Temporizadores para ejecutar tareas a intervalos regulares ---
extern unsigned long lastPI;   // Último cálculo del control térmico (cada 1000 ms)
extern unsigned long lastRamp; // Último incremento de la rampa de arranque (cada 200 ms)
extern unsigned long lastPH;   // Última lectura de pH (cada 20 ms)
extern unsigned long lastEnv;  // Última lectura ambiental (cada 5000 ms)

#endif // CONFIG_H
