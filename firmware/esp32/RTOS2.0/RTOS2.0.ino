/**
 * =================================================================================
 * CONTROLADOR MAESTRO DE ELECTRODEPOSICIÓN (RTOS2.0.ino)
 * =================================================================================
 * Plataforma: ESP32-S3 N16R8 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 * Sistema Operativo: FreeRTOS SMP (Symmetric Multiprocessing)
 *
 * ASIGNACIÓN DE RECURSOS POR NÚCLEO:
 * 1. Core 1 (Control de Hardware y Tiempo Real):
 *    - Task_Supervisor (Prioridad 6): Watchdog software 50 Hz y enclavamiento Fail-Safe.
 *    - Task_Termico    (Prioridad 5): Lazos PI térmicos (4 tinas) y enlace UART2 a Nano.
 *    - Task_Fuente     (Prioridad 4): Modulación de corriente VCSS (DC/Pulsado 1-100 Hz).
 *    - Task_Sensado    (Prioridad 3): Adquisición ADS1115 (pH y shunts) y sensores ambientales.
 *
 * 2. Core 0 (Comunicaciones y Pila de Red):
 *    - Task_Web        (Prioridad 2): Servidor HTTP, endpoints REST JSON y servicio OTA.
 *
 * CONFIGURACIÓN DE COMPILACIÓN (Arduino IDE):
 * - Placa: "ESP32S3 Dev Module"
 * - Flash: 16 MB (QIO 80 MHz), Partición: 3 MB APP / 9.9 MB FATFS
 * - PSRAM: OPI PSRAM habilitada
 * - USB CDC On Boot: Enabled
 * =================================================================================
 */

#include <ESPmDNS.h>
#include "config.h"
#include "RTOS_Core.h"
#include "Modulo_Termico.h"
#include "Modulo_Fuentes.h"
#include "Modulo_PH.h"
#include "Modulo_Ambiental.h"
#include "Modulo_OTA.h"
#include "WebServer_App.h"
#include "Task_Supervisor.h"
#include "Task_Termico.h"
#include "Task_Fuente.h"
#include "Task_Sensado.h"
#include "Task_Web.h"

// =================================================================================
// ASIGNACIÓN DE VARIABLES GLOBALES (`extern` en config.h)
// =================================================================================

/** @brief Credenciales de la red inalámbrica generada directamente por el ESP32 */
const char *ssid = "Uli";
const char *password = "12345678";

/** @brief Instancia del servidor HTTP en el puerto estándar 80 */
WebServer server(80);

/** @brief Gestor de memoria no volátil Flash (NVS) para almacenamiento de parámetros */
Preferences memoria;

/** @brief Convertidor Analógico/Digital I2C de 16 bits ADS1115 (A1: pH Dedicado, A2/A3: Shunts) */
Adafruit_ADS1115 ads;

/** @brief Convertidor Digital/Analógico I2C de 12 bits MCP4725 para consigna VCSS */
Adafruit_MCP4725 dac;

// Variables de Sensado Ambiental (Estación Meteorológica Local)
volatile float amb_temp = 0.0f;  /**< Temperatura ambiente de laboratorio en °C */
volatile float amb_hum  = 0.0f;  /**< Humedad relativa ambiente en % */
volatile float amb_pres = 0.0f;  /**< Presión atmosférica en hPa */

// Variables del Módulo de Medición y Calibración de pH (RTOS 2.0 - Sensor Dedicado Canal A1)
volatile bool    phModuloActivo = false;  /**< Habilita el muestreo del ADC para pH */
volatile uint8_t tipoCalPH = 0;           /**< Modo de calibración (0:Teórico, 1:2-Puntos, 2:3-Puntos) */
volatile float   v7_ph = PH_OFFSET_TEORICO, v4_ph = 2.0f, v10_ph = 1.3f; /**< Puntos de calibración (V) */
volatile float   m_ph = PH_PENDIENTE_TEORICA, mAcida_ph = PH_PENDIENTE_TEORICA, mBasica_ph = PH_PENDIENTE_TEORICA;
volatile float   phActual = 7.0f;         /**< Lectura procesada y filtrada para sensor dedicado */
volatile bool    calibradoPH = true;      /**< Bandera de validez metrológica */
volatile float   voltajeADC_ph = PH_OFFSET_TEORICO; /**< Voltaje analógico en entrada ADS1115 Canal A1 (V) */
volatile float   voltajeSonda_ph = 2.50f; /**< Voltaje real acondicionado de sonda (V) */
volatile float   voltajeCrudoPH = PH_OFFSET_TEORICO; /**< Voltaje directo de la sonda para diagnóstico */

// Variables de la Salida de Corriente VCSS (Sumidero Lineal + Shunts)
volatile bool  fuenteActiva = false;             /**< Estado operativo de la salida de corriente */
volatile bool  modoPulsado = false;              /**< false: Continua (DC), true: Onda cuadrada pulsada */
volatile int   amplitudDAC = 1024;               /**< Código digital aplicado al DAC MCP4725 (0..4095) */
volatile int   amplitudDAC_Setpoint = 1024;      /**< Consigna objetivo solicitada por el usuario (bits) */
volatile int   frecuencia = 10;                  /**< Frecuencia de pulsado en Hz (1..100 Hz) */
volatile int   dutyCycle = 50;                   /**< Ciclo de trabajo en % (0..100%) */
volatile bool  estadoReleVDD = false;            /**< Estado físico del relé ZCS de +12V (GPIO 20) */
volatile float corrienteReal_R1 = 0.0f;          /**< Corriente medida en Rama 1 (Amperios) */
volatile float corrienteReal_R2 = 0.0f;          /**< Corriente medida en Rama 2 (Amperios) */
volatile float corrienteTotalReal = 0.0f;        /**< Corriente total entregada a la celda (I1 + I2) */
volatile float voltajeShunt1_raw = 0.0f;         /**< Caída de potencial analógica en Shunt 1 (V) */
volatile float voltajeShunt2_raw = 0.0f;         /**< Caída de potencial analógica en Shunt 2 (V) */
volatile float factorGananciaVCSS = 1.000f;      /**< Factor de calibración de transconductancia (Gm) */
volatile bool  compensacionLazoCerrado = false;  /**< Habilita el recorte digital automático de ganancia */
volatile uint8_t estadoPICorriente = PI_STATE_OFF;/**< Estado operativo del lazo PI de corriente */
volatile uint8_t estadoSaludCelda = CELDA_OK;    /**< Diagnóstico de salud de la celda de electrodeposición */
volatile float   s_ondaETS[ETS_NUM_PUNTOS] = {0.0f}; /**< Array estroboscópico de onda de corriente reconstruida */
volatile float   energiaTermicaTotal_Wh = 0.0f;  /**< Energía acumulada en calentadores térmicos (Wh) */

// =================================================================================
// FUNCIÓN PRINCIPAL DE ARRANQUE E INICIALIZACIÓN (SETUP)
// =================================================================================

void setup() {
  // 1. Consola Serie USB CDC para monitoreo y depuración
  Serial.begin(115200);
  delay(800);
  Serial.println("\n==================================================");
  Serial.println("  INICIALIZANDO ESP32 — ARQUITECTURA FULL FREERTOS");
  Serial.printf( "  FIRMWARE v%s — RTOS 2.0 SENSOR PH DEDICADO (CANAL A1)\n", FIRMWARE_VERSION);
  Serial.println("  Developed by Salvador² C");
  Serial.println("==================================================");

  // 2. UART2 hacia microcontrolador Arduino Nano esclavo (TX Pin 17 @ 9600 bps)
  Serial2.begin(9600, SERIAL_8N1, -1, PIN_UART2_TX);
  Serial.println("[UART] Puente con Arduino Nano listo en TX GPIO 17 (9600 bps).");

  // 3. Inicialización del bus I2C con resistencias pull-up internas
  pinMode(PIN_I2C_SDA, INPUT_PULLUP);
  pinMode(PIN_I2C_SCL, INPUT_PULLUP);
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(400000); // 400 kHz: Fast Mode I2C
  Wire.setTimeOut(50);
  Serial.println("[I2C] Bus I2C iniciado en SDA=GPIO8, SCL=GPIO9 a 400 kHz (Fast Mode).");

  // 4. Inicialización del núcleo RTOS
  rtosInicializarNucleo();

  // 5. Carga de parámetros operacionales desde memoria Flash no volátil (NVS)
  memoria.begin("config", false);

  if (takeDataMutex(pdMS_TO_TICKS(100))) {
    // Restaurar consignas de temperatura para las 4 tinas
    for (int i = 0; i < 4; i++) {
      char key[16];
      snprintf(key, sizeof(key), "sp%d", i);
      float spG = memoria.getFloat(key, canales[i].setpoint);
      if (spG <= 0.0f || spG > 150.0f) spG = 60.0f;
      canales[i].setpoint = spG;
    }

    // Restaurar calibración de pH para Sensor Único Dedicado en Canal A1 (con fallback retrocompatible)
    tipoCalPH = memoria.getUChar("tcal", memoria.getUChar("tcal1", 0));
    if (tipoCalPH > 2) tipoCalPH = 0;
    v7_ph = memoria.getFloat("v7", memoria.getFloat("v7_1", PH_OFFSET_TEORICO));
    v4_ph = memoria.getFloat("v4", memoria.getFloat("v4_1", 2.0f));
    v10_ph = memoria.getFloat("v10", memoria.getFloat("v10_1", 1.3f));
    float savedM = memoria.getFloat("mph", memoria.getFloat("mph1", PH_PENDIENTE_TEORICA));
    m_ph = (savedM < 0.0f) ? -savedM : savedM;
    float savedMAc = memoria.getFloat("mAc", memoria.getFloat("mAc1", PH_PENDIENTE_TEORICA));
    mAcida_ph = (savedMAc < 0.0f) ? -savedMAc : savedMAc;
    float savedMBa = memoria.getFloat("mBa", memoria.getFloat("mBa1", PH_PENDIENTE_TEORICA));
    mBasica_ph = (savedMBa < 0.0f) ? -savedMBa : savedMBa;
    calibradoPH = memoria.getBool("cal", memoria.getBool("cal1", true));
    if (tipoCalPH == 0) calibradoPH = true;

    phModuloActivo = false; // El módulo de pH siempre arranca en reposo por seguridad

    // Restaurar configuración de la salida de corriente VCSS
    amplitudDAC = memoria.getInt("dac_amp", 1024);
    amplitudDAC_Setpoint = amplitudDAC;
    frecuencia = memoria.getInt("dac_freq", 10);
    dutyCycle = memoria.getInt("dac_duty", 50);
    modoPulsado = memoria.getBool("dac_modo", false);
    fuenteActiva = false;

    giveDataMutex();
  }

  Serial.println("[NVS] Parámetros cargados desde Flash con éxito.");

  // 6. Inicialización de submódulos de instrumentación y potencia
  inicializarModuloTermico();
  inicializarFuente();
  inicializarModuloPH();
  bool envOK = inicializarModuloAmbiental();

  // 7. Configuración del punto de acceso Wi-Fi local (SoftAP)
  Serial.printf("[WiFi AP] Creando red Wi-Fi propia (SSID: %s)...\n", ssid);
  WiFi.mode(WIFI_AP);
  bool wifiOK = WiFi.softAP(ssid, password);
  WiFi.setSleep(false);
  Serial.print("[WiFi AP] Dirección IP local: ");
  Serial.println(WiFi.softAPIP());

  // Interlock Fail-Safe de arranque
  if (!wifiOK) {
    triggerFailSafe(ERR_WIFI_FAIL, "Falla crítica en arranque de Red Wi-Fi SoftAP");
  } else if (!envOK) {
    Serial.println("[AMBIENTAL] ⚠️ Advertencia: Sensores ambientales ausentes. Operando en modo degradado.");
  }

  // 8. Servicio mDNS
  if (MDNS.begin("interfaz")) {
    Serial.println("[mDNS] Servicio mDNS activo en http://interfaz.local");
  }

  // 9. Registro de rutas HTTP e inicio del servidor web en puerto 80
  inicializarWebServer();

  // 10. Despliegue de Tareas Concurrentes en FreeRTOS
  Serial.println("\n[FREERTOS] Lanzando tareas concurrentes...");
  iniciarTaskSupervisor(); // Core 1, Prio 6
  iniciarTaskTermico();    // Core 1, Prio 5
  iniciarTaskFuente();     // Core 1, Prio 4
  iniciarTaskSensado();    // Core 1, Prio 3
  iniciarTaskWeb();        // Core 0, Prio 2

  Serial.println("==================================================");
  Serial.println("  SISTEMA OPERATIVO Y CONCURRENTE — ESP32 RTOS 2.0");
  Serial.println("==================================================\n");
}

// =================================================================================
// BUCLE PRINCIPAL DE ARDUINO (YIELD PERMANENTE)
// =================================================================================

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}
