#ifndef CONFIG_H
#define CONFIG_H

/**
 * =================================================================================
 * CONFIGURACIÓN GLOBAL DEL SISTEMA (config.h)
 * =================================================================================
 * Este archivo centraliza todo lo que los demás archivos del proyecto necesitan
 * compartir: las librerías comunes, las constantes de pines del circuito, y la
 * lista de variables globales que se usan desde varios lugares del programa.
 *
 * ¿POR QUÉ EXISTE ESTE ARCHIVO?
 * En un proyecto con varios archivos .cpp, cada uno necesita saber qué
 * variables y objetos existen en los otros. Este archivo actúa como un
 * "contrato" que declara todo lo compartido en un solo lugar, evitando
 * duplicaciones y errores.
 *
 * MAPA DE CONEXIONES DEL ESP32 (PINES FÍSICOS DEL CIRCUITO):
 * ---------------------------------------------------------------------------------
 * PERIFÉRICO          | PIN ESP32 | FUNCIÓN
 * ---------------------------------------------------------------------------------
 * I2C (SDA)           | GPIO 8    | Datos I2C (ADS1115, MCP4725, AHT20, BMP280)
 * I2C (SCL)           | GPIO 9    | Reloj I2C (400 kHz)
 * SPI Termopares      | GPIO 18   | Reloj SPI compartido para 4 sensores
 * MAX6675 SPI Termopares      | GPIO 19   | Datos SPI compartido para 4
 * sensores MAX6675 CS Termopar 0       | GPIO 5    | Selector del sensor de
 * Tina Limpieza CS Termopar 1       | GPIO 4    | Selector del sensor de Tina
 * Decapado CS Termopar 2       | GPIO 13   | Selector del sensor de Celda Hull
 * CS Termopar 3       | GPIO 14   | Selector del sensor de Tina Niquelado
 * UART2 (TX)          | GPIO 17   | Envío de datos serie al Arduino Nano (9600
 * baud)
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

// Candados de sincronización para acceso concurrente desde el Servidor Web
extern portMUX_TYPE muxFuente;
extern portMUX_TYPE muxPH;

// =================================================================================
// OBJETOS GLOBALES DE RED Y ALMACENAMIENTO (creados en Proyecto.ino)
// =================================================================================
extern const char *ssid;     // Nombre de la red Wi-Fi que crea el ESP32
extern const char *password; // Contraseña de la red Wi-Fi
extern WebServer server; // Servidor web para la interfaz de control (puerto 80)
extern Preferences
    memoria; // Almacenamiento en memoria Flash para guardar configuraciones

// =================================================================================
// CONSTANTES DE PINES Y HARDWARE
// =================================================================================

// Voltaje de referencia del circuito impreso (3.3V). Se define aquí como
// constante de referencia del hardware por si se necesita en cálculos futuros.
#define VREF 3.3

// Pines SPI compartidos por los 4 amplificadores de termopar MAX6675
#define COMMON_SCK 18 // Reloj SPI (GPIO 18)
#define COMMON_SO 19  // Datos SPI (GPIO 19)

// =================================================================================
// SENSORES Y CONVERTIDORES EN EL BUS I2C (creados en sus respectivos módulos)
// =================================================================================
extern Adafruit_AHTX0
    aht; // Sensor de temperatura y humedad (dirección I2C 0x38)
extern Adafruit_BMP280
    bmp; // Sensor de presión atmosférica (dirección I2C 0x76 o 0x77)
extern Adafruit_ADS1115
    ads; // Convertidor analógico-digital de 16 bits para sondas pH (0x48)
extern Adafruit_MCP4725
    dac; // Convertidor digital-analógico de 12 bits para corriente (0x60)

// =================================================================================
// VARIABLES GLOBALES COMPARTIDAS
// =================================================================================
// La palabra "volatile" le indica al compilador que estas variables pueden
// cambiar en cualquier momento (por ejemplo, cuando el servidor web recibe un
// comando del usuario), así que debe leerlas siempre de la memoria en lugar de
// usar copias viejas.

// --- Monitoreo Ambiental (se actualizan cada 5 segundos) ---
extern volatile float amb_temp; // Temperatura ambiente en °C (sensor AHT20)
extern volatile float amb_hum;  // Humedad relativa en % (sensor AHT20)
extern volatile float amb_pres; // Presión atmosférica en hPa (sensor BMP280)

// --- Módulo de pH Dual (2 sondas, una por tina) ---
// Tina 1 (Zincado)
extern volatile float v7_1; // Voltaje medido al sumergir en solución pH 7.0
extern volatile float v4_1; // Voltaje medido al sumergir en solución pH 4.0
extern volatile float
    m_ph1; // Pendiente de la recta de calibración (pH por Voltio)
extern volatile float phActual1; // Lectura de pH en tiempo real
extern volatile bool
    calibradoPH1; // true si se completó la calibración de 2 puntos

// Tina 2 (Niquelado)
extern volatile float v7_2;
extern volatile float v4_2;
extern volatile float m_ph2;
extern volatile float phActual2;
extern volatile bool calibradoPH2;

// --- Fuente de Corriente (DAC MCP4725) ---
extern volatile bool fuenteActiva; // true = salida de corriente encendida
extern volatile bool
    modoPulsado; // true = corriente pulsada, false = corriente continua
extern volatile int
    amplitudDAC; // Valor digital del DAC (0-4095, donde 4095 = 6.6 A máx)
extern volatile int frecuencia; // Frecuencia de pulso en Hz (1-100 Hz)
extern volatile int dutyCycle;  // Porcentaje del tiempo en nivel alto (0-100 %)

// --- Temporizadores para ejecutar tareas a intervalos regulares ---
// Estas variables guardan el momento (en milisegundos) en que se ejecutó cada
// tarea por última vez, permitiendo medir cuándo toca ejecutarla de nuevo sin
// usar delay().
extern unsigned long
    lastPI; // Último cálculo del control térmico (cada 1000 ms)
extern unsigned long
    lastRamp; // Último incremento de la rampa de arranque (cada 200 ms)
extern unsigned long lastPH;  // Última lectura de pH (cada 20 ms)
extern unsigned long lastEnv; // Última lectura ambiental (cada 5000 ms)

#endif // CONFIG_H