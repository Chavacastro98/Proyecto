/**
 * =================================================================================
 * PROYECTO PRINCIPAL DE ELECTRODEPOSICIÓN — Versión RTOS 1.1 (RTOS1.1.ino)
 *
 * MEJORAS v1.1 (Interfaz Web — Feedback Visual):
 *   • Heartbeat de conectividad en tiempo real con indicador de latencia
 *   • Animación de conteo suave en valores numéricos (corriente, pH, temp.)
 *   • Indicadores de tendencia térmica (↑↓→) con delta numérico
 *   • Barra VU analógica en el amperímetro digital VCSS
 *   • Toast notifications animadas (reemplazan alert() nativos)
 *   • Indicador visual de pulso rítmico en modo pulsado
 *   • Barra de progreso hacia setpoint con gradiente de color
 *   • Micro-animaciones de estado en botones y tarjetas
 *   • Estado en vivo de cada módulo visible desde el menú principal
 * =================================================================================
 * Arquitectura: ESP32 Master Controller / FreeRTOS SMP Dual-Core + MVC Web Modular
 * Microcontrolador: ESP32-S3 N16R8 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz, 16MB Flash, 8MB PSRAM)
 *
 * PROPÓSITO GENERAL DEL SISTEMA:
 * Control determinista y concurrente en tiempo real para planta de electrodeposición
 * y análisis electroquímico, estructurado en dos dominios de ejecución asimétricos:
 *
 * 1. NÚCLEO DE TIEMPO REAL (Core 1 — Hardware Crítico):
 *    - Task_Supervisor (Prioridad 6): Watchdog software 50 Hz, control de baliza LED RGB
 *      y gestión centralizada del enclavamiento de seguridad "Fail-Safe Latch".
 *    - Task_Termico (Prioridad 5): 4 Lazos de control PI discretos (450W por celda),
 *      lectura SPI de termopares MAX6675 y comunicación UART2 con Arduino Nano.
 *    - Task_Fuente (Prioridad 4): Modulador de corriente VCSS en modo continuo (DC) y
 *      pulsado (1-100 Hz), conmutación segura ZCS de relé de +12V y muestreo estroboscópico.
 *    - Task_Sensado (Prioridad 3): Adquisición periódica de pH dual (ADS1115 A0/A1),
 *      sensado de corriente en shunts (A2/A3) y meteorología ambiental (AHT20/BMP280).
 *
 * 2. NÚCLEO DE COMUNICACIONES (Core 0 — Servidor y Pila de Red):
 *    - Task_Web (Prioridad 2): Servidor HTTP no bloqueante (Puerto 80), endpoints JSON REST,
 *      telemetría en tiempo real y actualización inalámbrica de firmware (OTA).
 *
 * CONFIGURACIÓN DE COMPILACIÓN (Hardware ESP32-S3 N16R8):
 * - Board: "ESP32S3 Dev Module"
 * - Flash Size: "16MB (128Mb)"
 * - Partition Scheme: "16M Flash (3MB APP/9.9MB FATFS)"
 * - PSRAM: "OPI PSRAM"
 * - Flash Mode: "QIO 80MHz"
 * - USB CDC On Boot: "Enabled"
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

/** @brief Convertidor Analógico/Digital I2C de 16 bits ADS1115 (A0..A3) */
Adafruit_ADS1115 ads;

/** @brief Convertidor Digital/Analógico I2C de 12 bits MCP4725 para consigna VCSS */
Adafruit_MCP4725 dac;

// Variables de Sensado Ambiental (Estación Meteorológica Local)
volatile float amb_temp = 0.0f;  /**< Temperatura ambiente de laboratorio en °C */
volatile float amb_hum  = 0.0f;  /**< Humedad relativa ambiente en % */
volatile float amb_pres = 0.0f;  /**< Presión atmosférica en hPa */

// Variables del Módulo de Medición y Calibración de pH Dual
volatile bool    phModuloActivo = false;  /**< Habilita el muestreo del ADC para pH */
volatile uint8_t tipoCalPH1 = 0, tipoCalPH2 = 0;  /**< Modo de calibración (0:Teórico, 1:2-Puntos, 2:3-Puntos) */
volatile float   v7_1 = PH_OFFSET_TEORICO, v4_1 = 2.0f, v10_1 = 1.3f; /**< Puntos de calibración Tina 1 (V) */
volatile float   m_ph1 = -PH_PENDIENTE_TEORICA, mAcida1 = -PH_PENDIENTE_TEORICA, mBasica1 = -PH_PENDIENTE_TEORICA;
volatile float   phActual1 = 7.0f;  /**< Lectura procesada y filtrada para Tina 1 */
volatile bool    calibradoPH1 = false; /**< Bandera de validez metrológica Tina 1 */

volatile float   v7_2 = PH_OFFSET_TEORICO, v4_2 = 2.0f, v10_2 = 1.3f; /**< Puntos de calibración Tina 2 (V) */
volatile float   m_ph2 = -PH_PENDIENTE_TEORICA, mAcida2 = -PH_PENDIENTE_TEORICA, mBasica2 = -PH_PENDIENTE_TEORICA;
volatile float   phActual2 = 7.0f;  /**< Lectura procesada y filtrada para Tina 2 */
volatile bool    calibradoPH2 = false; /**< Bandera de validez metrológica Tina 2 */

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

// =================================================================================
// FUNCIÓN PRINCIPAL DE ARRANQUE E INICIALIZACIÓN (SETUP)
// =================================================================================

void setup() {
  // 1. Consola Serie USB CDC para monitoreo y depuración
  Serial.begin(115200);
  delay(800);
  Serial.println("\n==================================================");
  Serial.println("  INICIALIZANDO ESP32 — ARQUITECTURA FULL FREERTOS");
  Serial.printf( "  FIRMWARE v%s — SMP DUAL-CORE + FAIL-SAFE LATCH\n", FIRMWARE_VERSION);
  Serial.println("  Developed by Salvador² C");
  Serial.println("==================================================");

  // 2. UART2 hacia microcontrolador Arduino Nano esclavo (TX Pin 17 @ 9600 bps)
  // Encargado de disparar los TRIACs en cruce por cero para el calentamiento de 450W
  Serial2.begin(9600, SERIAL_8N1, -1, PIN_UART2_TX);
  Serial.println("[UART] Puente con Arduino Nano listo en TX GPIO 17 (9600 bps).");

  // 3. Inicialización del bus I2C con resistencias pull-up internas para evitar bus flotante
  pinMode(PIN_I2C_SDA, INPUT_PULLUP);
  pinMode(PIN_I2C_SCL, INPUT_PULLUP);
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(400000); // 400 kHz: Fast Mode I2C (reduce la contención temporal en mutex)
  Wire.setTimeOut(50);   // Timeout de 50 ms para recuperar el bus ante pulsos anómalos
  Serial.println("[I2C] Bus I2C iniciado en SDA=GPIO8, SCL=GPIO9 a 400 kHz (Fast Mode).");

  // 4. Inicialización del núcleo RTOS (Creación de Mutexes, Watchdog y Ring Buffer)
  rtosInicializarNucleo();

  // 5. Carga de parámetros operacionales desde memoria Flash no volátil (NVS)
  memoria.begin("config", false);

  if (takeDataMutex(pdMS_TO_TICKS(100))) {
    // Restaurar consignas de temperatura para las 4 tinas
    for (int i = 0; i < 4; i++) {
      char key[16];
      snprintf(key, sizeof(key), "sp%d", i);
      float spG = memoria.getFloat(key, canales[i].setpoint);
      if (spG <= 0.0f || spG > 150.0f) spG = 60.0f; // Salvaguarda en 60°C por defecto
      canales[i].setpoint = spG;
    }

    // Restaurar calibración de pH para Tina 1
    tipoCalPH1 = memoria.getUChar("tcal1", 0);
    if (tipoCalPH1 > 2) tipoCalPH1 = 0;
    v7_1 = memoria.getFloat("v7_1", PH_OFFSET_TEORICO);
    v4_1 = memoria.getFloat("v4_1", 2.0f);
    v10_1 = memoria.getFloat("v10_1", memoria.getFloat("v11_1", 1.3f));
    m_ph1 = memoria.getFloat("mph1", -PH_PENDIENTE_TEORICA);
    mAcida1 = memoria.getFloat("mAc1", -PH_PENDIENTE_TEORICA);
    mBasica1 = memoria.getFloat("mBa1", -PH_PENDIENTE_TEORICA);
    calibradoPH1 = memoria.getBool("cal1", false);
    if (tipoCalPH1 == 0) calibradoPH1 = true;

    // Restaurar calibración de pH para Tina 2
    tipoCalPH2 = memoria.getUChar("tcal2", 0);
    if (tipoCalPH2 > 2) tipoCalPH2 = 0;
    v7_2 = memoria.getFloat("v7_2", PH_OFFSET_TEORICO);
    v4_2 = memoria.getFloat("v4_2", 2.0f);
    v10_2 = memoria.getFloat("v10_2", memoria.getFloat("v11_2", 1.3f));
    m_ph2 = memoria.getFloat("mph2", -PH_PENDIENTE_TEORICA);
    mAcida2 = memoria.getFloat("mAc2", -PH_PENDIENTE_TEORICA);
    mBasica2 = memoria.getFloat("mBa2", -PH_PENDIENTE_TEORICA);
    calibradoPH2 = memoria.getBool("cal2", false);
    if (tipoCalPH2 == 0) calibradoPH2 = true;

    phModuloActivo = false; // El módulo de pH siempre arranca inactivo por seguridad

    // Restaurar configuración de la salida de corriente VCSS
    amplitudDAC = memoria.getInt("dac_amp", 1024);
    amplitudDAC_Setpoint = amplitudDAC;
    frecuencia = memoria.getInt("dac_freq", 10);
    dutyCycle = memoria.getInt("dac_duty", 50);
    modoPulsado = memoria.getBool("dac_modo", false);
    fuenteActiva = false; // La fuente siempre arranca apagada por seguridad física

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
  WiFi.setSleep(false); // Desactiva el ahorro de energía para garantizar tasa de transferencia continua
  Serial.print("[WiFi AP] Dirección IP local: ");
  Serial.println(WiFi.softAPIP());

  // Interlock Fail-Safe de arranque si no fue posible levantar la radio Wi-Fi
  if (!wifiOK) {
    triggerFailSafe(ERR_WIFI_FAIL, "Falla crítica en arranque de Red Wi-Fi SoftAP");
  } else if (!envOK) {
    Serial.println("[AMBIENTAL] ⚠️ Advertencia: Sensores ambientales ausentes. Operando en modo degradado.");
  }

  // 8. Servicio mDNS para resolución de nombre local (http://interfaz.local)
  if (MDNS.begin("interfaz")) {
    Serial.println("[mDNS] Servicio mDNS activo en http://interfaz.local");
  }

  // 9. Registro de rutas HTTP e inicio del servidor web en puerto 80
  inicializarWebServer();

  // 10. Despliegue y fijación de Tareas Concurrentes en FreeRTOS
  // Core 1 (Tiempo Real): Prioridades 6 (Supervisor) > 5 (Térmico) > 4 (Fuente) > 3 (Sensado)
  // Core 0 (Comunicaciones): Prioridad 2 (Servidor Web y Pila lwIP)
  Serial.println("\n[FREERTOS] Lanzando tareas concurrentes...");
  iniciarTaskSupervisor(); // Core 1, Prio 6
  iniciarTaskTermico();    // Core 1, Prio 5
  iniciarTaskFuente();     // Core 1, Prio 4
  iniciarTaskSensado();    // Core 1, Prio 3
  iniciarTaskWeb();        // Core 0, Prio 2

  Serial.println("==================================================");
  Serial.println("  SISTEMA OPERATIVO Y CONCURRENTE — ESP32 RTOS 1.0");
  Serial.println("==================================================\n");
}

// =================================================================================
// BUCLE PRINCIPAL DE ARDUINO (YIELD PERMANENTE)
// =================================================================================

/**
 * @brief En una arquitectura pura FreeRTOS, el bucle loop() tradicional queda libre.
 * Para no consumir ciclos de CPU de forma inútil ni disparar el Watchdog de la tarea loopTask,
 * cedemos el procesador suspendiendo la ejecución por 1000 ms en cada iteración.
 */
void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}

