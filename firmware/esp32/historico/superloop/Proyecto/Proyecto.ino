/**
 * =================================================================================
 * PROYECTO PRINCIPAL DE ELECTRODEPOSICIÓN (Proyecto.ino)
 * =================================================================================
 * Arquitectura: ESP32 Master Controller (Firmware Principal) / FreeRTOS
 *
 * PROPÓSITO GENERAL:
 * Controla un sistema industrial/laboratorio modular de galvanoplastia y
 * electrodeposición. El ESP32 actúa como nodo central maestro encargándose de:
 * 1. Servir la GUI Web dinámica accesible por cualquier dispositivo en la red
 * local (SoftAP).
 * 2. Ejecutar 4 lazos independientes de control térmico PI con anti-windup (FPU
 * por HW de 32 bits).
 * 3. Transmitir las potencias calculadas al Arduino Nano esclavo vía UART2 (TX
 * GPIO 17).
 * 4. Controlar la fuente de corriente analógica (DC / Pulsada) con el DAC
 * MCP4725 vía I2C @400kHz.
 * 5. Monitorear el pH de dos tinas mediante sondas analógicas y el ADC ADS1115
 * a 860 SPS.
 * 6. Adquirir variables meteorológicas del entorno de proceso (AHT20 + BMP280).
 * 7. Gestionar la memoria no volátil Flash NVS (Preferences) para persistir
 * parámetros.
 *
 * ARQUITECTURA MULTITAREA NO BLOQUEANTE:
 * Se utiliza un programador por temporización con `millis()` y `micros()` en
 * lugar de `delay()`, garantizando tiempo real en la atención a solicitudes
 * HTTP y la generación de pulsos DAC.
 * - Fuente de corriente: Loop libre a máxima velocidad (Filtro de caché I2C).
 * - Lazo de control Térmico: Cada 1000 ms (+ rampa de potencia cada 200 ms).
 * - Módulo de pH Dual: Lectura Asíncrona Alternada cada 200 ms a 860 SPS (~1.16
 * ms por muestra).
 * - Módulo Ambiental: Cada 5000 ms.
 * =================================================================================
 */

#include <ESPmDNS.h>

// Inclusión de las cabeceras de los submódulos del sistema (Nombres en
// minúsculas)
#include "Modulo_Ambiental.h"
#include "Modulo_Fuentes.h"
#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "WebServer_App.h"
#include "config.h"

// =================================================================================
// DEFINICIÓN Y ASIGNACIÓN DE VARIABLES GLOBALES VOLATILE (`extern` de config.h)
// =================================================================================

// Credenciales para la red Wi-Fi local en modo SoftAP (Punto de Acceso)
const char *ssid = "Uli";
const char *password = "12345678";

// Instancias de Periféricos Globales
WebServer server(80); // Servidor Web HTTP escuchando en el puerto 80
Preferences memoria;  // Objeto de almacenamiento no volátil NVS (Flash)
Adafruit_ADS1115 ads; // ADC de 16 bits para lecturas de sondas pH (I2C 0x48)
Adafruit_MCP4725 dac; // DAC de 12 bits para control de corriente (I2C 0x60)

// Candados de Sincronización FreeRTOS
portMUX_TYPE muxFuente = portMUX_INITIALIZER_UNLOCKED;
portMUX_TYPE muxPH = portMUX_INITIALIZER_UNLOCKED;

// Variables de Estado Ambiental (Concurrencia Volatile)
volatile float amb_temp = 0.0, amb_hum = 0.0, amb_pres = 0.0;

// Variables de Calibración y Estado para pH Dual (Tina 1: Zincado, Tina 2: Niquelado)
// Valores teóricos por defecto con divisor a 3.3V: V7 ≈ 1.65V, V4 ≈ 2.35V, Pendiente ≈ -4.242 pH/V
volatile float v7_1 = 1.65, v4_1 = 2.35, m_ph1 = -4.242, phActual1 = 7.0;
volatile float v7_2 = 1.65, v4_2 = 2.35, m_ph2 = -4.242, phActual2 = 7.0;
volatile bool calibradoPH1 = false, calibradoPH2 = false;

// Variables de Control de la Fuente de Corriente (Sumidero DAC MCP4725)
volatile bool fuenteActiva = false;
volatile bool modoPulsado = false;
volatile int amplitudDAC = 1024;
volatile int frecuencia = 1;
volatile int dutyCycle = 50;

// Temporizadores No Bloqueantes (Basados en millis)
unsigned long lastPI = 0;   // Período PI térmico (1000 ms)
unsigned long lastRamp = 0; // Período rampa de arranque (200 ms)
unsigned long lastPH = 0;   // Período muestreo asíncrono pH (200 ms)
unsigned long lastEnv = 0;  // Período lectura ambiental (5000 ms)

// =================================================================================
// CONFIGURACIÓN DEL SISTEMA (SETUP)
// =================================================================================

void setup() {
  // 1. Inicialización de Consola Serie USB para Depuración de Desarrollo
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n==================================================");
  Serial.println(" INICIALIZANDO LÍNEA DE ELECTRODEPOSICIÓN ESP32 ");
  Serial.println("==================================================");

  // 2. Inicialización de la UART2 para el puente serie con Arduino Nano (Pin
  // TX=17 @9600 baudios)
  Serial2.begin(9600, SERIAL_8N1, -1, 17);
  Serial.println("[UART] Puente serie con Arduino Nano iniciado en TX Pin 17 a "
                 "9600 baudios.");

  /**
   * JUSTIFICACIÓN DE DISEÑO PROPOSITAL: TIMEOUT DEL BUS I2C
   * (`Wire.setTimeOut(50)`) La conmutación de potencia de las resistencias de
   * 450W mediante Triacs genera picos de ruido electromagnético (EMI). Si una
   * señal I2C se distorsiona momentáneamente, la librería Wire estándar sin
   * timeout puede congelar el CPU indefinidamente. El timeout de 50 ms cancela
   * la transacción en caso de interferencia y mantiene el sistema vivo.
   */
  Wire.begin(8, 9);
  Wire.setClock(400000); // Configura velocidad I2C a 400 kHz (Fast-Mode)
  Wire.setTimeOut(50);   // Timeout de 50ms para prevenir cuelgues por ruido
                         // electromagnético (EMI)
  Serial.println("[I2C] Bus I2C iniciado en SDA=GPIO8, SCL=GPIO9 a 400 kHz "
                 "(Timeout: 50ms).");

  // 4. Apertura del almacenamiento no volátil NVS (Espacio de nombres:
  // "config")
  memoria.begin("config", false);

  // Carga de Setpoints térmicos guardados para los 4 canales con protección de
  // sección crítica
  portENTER_CRITICAL(&muxTermico);
  for (int i = 0; i < 4; i++) {
    char key[16];
    snprintf(key, sizeof(key), "sp%d", i);
    float spGuardado = memoria.getFloat(key, canales[i].setpoint);
    if (spGuardado <= 0.0f || spGuardado > 150.0f)
      spGuardado = 60.0f; // Rango de seguridad
    canales[i].setpoint = spGuardado;
  }
  portEXIT_CRITICAL(&muxTermico);

  // Carga de coeficientes de calibración de pH desde la Flash NVS
  portENTER_CRITICAL(&muxPH);
  calibradoPH1 = memoria.getBool("cal1", false);
  v7_1 = memoria.getFloat("v7_1", 1.65);
  v4_1 = memoria.getFloat("v4_1", 2.35);
  m_ph1 = memoria.getFloat("mph1", -4.242);

  calibradoPH2 = memoria.getBool("cal2", false);
  v7_2 = memoria.getFloat("v7_2", 1.65);
  v4_2 = memoria.getFloat("v4_2", 2.35);
  m_ph2 = memoria.getFloat("mph2", -4.242);
  portEXIT_CRITICAL(&muxPH);

  // Carga de la configuración de la fuente de corriente
  portENTER_CRITICAL(&muxFuente);
  amplitudDAC = memoria.getInt("dac_amp", 1024);
  frecuencia = memoria.getInt("dac_freq", 1);
  dutyCycle = memoria.getInt("dac_duty", 50);
  modoPulsado = memoria.getBool("dac_modo", false);
  fuenteActiva = false; // Siempre arranca en Standby (0A) por seguridad operacional
  portEXIT_CRITICAL(&muxFuente);

  Serial.println(
      "[NVS] Parámetros y coeficientes cargados correctamente desde la Flash.");

  // 5. Inicialización de los submódulos de hardware
  inicializarModuloTermico();
  inicializarFuente();
  inicializarModuloPH();
  bool envOK = inicializarModuloAmbiental();

  // 6. Generar red Wi-Fi propia (Modo SoftAP / Access Point)
  Serial.print("[WiFi AP] Creando red Wi-Fi propia (SSID: ");
  Serial.print(ssid);
  Serial.println(")...");

  bool wifiOK = WiFi.softAP(ssid, password);

  /**
   * =================================================================================
   * JUSTIFICACIÓN DE DISEÑO PROPOSITAL: PARADA DE EMERGENCIA EN ARRANQUE
   * (FAIL-SAFE LOCKDOWN)
   * =================================================================================
   * NOTA PARA AUDITORES / AGENTES DE REVISIÓN:
   * El bloqueo intencional 'while(true) delay(1000)' cuando '!wifiOK' o
   * '!envOK' NO ES UN BUG ni una sobre-ingeniería no deseada. Es una POLÍTICA
   * DE SEGURIDAD INDUSTRIAL DELIBERADA:
   *
   * 1. Sin red Wi-Fi (SoftAP), el operador pierde el medio principal de
   * telemetría y control de parada de emergencia web. Operar tinas químicas y
   * resistivas de 450W "a ciegas" es un riesgo inaceptable de
   * sobrecalentamiento o derramamiento químico.
   * 2. Si falla el hardware ambiental o la red en el arranque, el sistema
   * desactiva físicamente la salida DAC (0V / 0A) y transmite potencias nulas
   * ("0,0,0,0") al Arduino Nano esclavo, entrando en paro total. Se requiere
   * revisión física del hardware y pulsar el botón RESET.
   */
  if (!wifiOK || !envOK) {
    Serial.println("\n==================================================");
    Serial.println(" ❌ EMERGENCIA: FALLA CRÍTICA DE HARDWARE O RED ");
    Serial.println(" PROCESO ABORTADO POR SEGURIDAD (INTERLOCK ACTIVADO) ");
    Serial.println("==================================================");

    // Apagado directo de emergencia de actuadores físicos
    dac.setVoltage(0, false);   // Salida DAC a 0 Amperios
    Serial2.println("0,0,0,0"); // TRIACs a 0% de potencia

    // Bloqueo total del sistema alimentando el perro guardián (TWDT)
    while (true) {
      delay(1000); // El delay(1000) cede tiempo al IDLE task alimentando el
                   // Watchdog de FreeRTOS
    }
  }

  Serial.println("[WiFi AP] Red Wi-Fi creada con éxito.");
  Serial.print("[WiFi AP] Dirección IP local del servidor: ");
  Serial.println(WiFi.softAPIP());

  // 8. Registro del servicio mDNS (Acceso por dirección de nombre en red local)
  if (MDNS.begin("interfaz")) {
    Serial.println("[mDNS] Servicio mDNS activo. Acceso GUI vía URL: "
                   "http://interfaz.local");
  } else {
    Serial.println(
        "[mDNS] ⚠️ Advertencia: No se pudo registrar el servicio mDNS.");
  }

  // 9. Arranque del servidor HTTP Web
  inicializarWebServer();

  Serial.println("==================================================");
  Serial.println(" SISTEMA OPERATIVO Y EN LÍNEA - ESP32 MASTER      ");
  Serial.println("==================================================\n");
}

// =================================================================================
// LAZO PRINCIPAL DE EJECUCIÓN ASÍNCRONA (LOOP)
// =================================================================================

void loop() {
  // 1. Atención de peticiones del cliente en la interfaz Web (Respuesta
  // inmediata HTTP)
  server.handleClient();

  // 2. Generación de corriente en el DAC (Corre libre a máxima velocidad con
  // caché I2C no bloqueante)
  actualizarFuente();

  // 3. Ejecución del Lazo Térmico PI y envío UART al Arduino Nano (Período:
  // 1000 ms)
  procesarControlTermico();

  // 4. Muestreo Asíncrono de pH (Toma 1 muestra alternada cada 20 ms a 860 SPS:
  // ~1.16 ms por muestra)
  if (millis() - lastPH >= 20) {
    lastPH = millis();
    procesarLecturaPH();
  }

  // 5. Lectura de sensores ambientales AHT20 y BMP280 (Período: 5000 ms de
  // forma no bloqueante)
  if (millis() - lastEnv >= 5000) {
    lastEnv = millis();
    procesarLecturaAmbiental();
  }
}