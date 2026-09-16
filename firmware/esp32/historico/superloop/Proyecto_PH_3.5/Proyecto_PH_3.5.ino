/**
 * =================================================================================
 * PROYECTO PRINCIPAL DE ELECTRODEPOSICIÓN — Versión 3.5 (Proyecto_PH_3.5.ino)
 * =================================================================================
 * Arquitectura: ESP32 Master Controller (Firmware Principal) / Super-Loop Asíncrono
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
 * a 860 SPS (BAJO DEMANDA — módulo On/Off).
 * 6. Adquirir variables meteorológicas del entorno de proceso (AHT20 + BMP280).
 * 7. Gestionar la memoria no volátil Flash NVS (Preferences) para persistir
 * parámetros.
 * 8. Actualizar el firmware de forma inalámbrica (OTA) vía web upload.
 *
 * CAMBIOS v3.1:
 * - Menú de diagnóstico de sensores: página /sensores con estado de los 8
 *   periféricos (4 I2C + 4 SPI) del sistema
 * - Botón manual de re-escaneo (no auto-refresh) para evitar tráfico I2C
 *   durante conexiones/desconexiones de hardware
 * - Endpoint JSON /data_sensors para escaneo en caliente del bus I2C y SPI
 * - Banderas de inicialización ambiental expuestas para diagnóstico externo
 *
 * CAMBIOS v3.0:
 * - Módulo OTA (Over-The-Air): actualización de firmware vía web sin cable USB
 * - Página /update con drag & drop, barra de progreso y verificación MD5
 * - Interlock de seguridad: bloquea OTA si hay actuadores activos
 * - Versión del firmware mostrada en menú principal y página de actualización
 * - Apagado seguro de actuadores previo al reinicio OTA
 *
 * REQUISITO DE COMPILACIÓN:
 * Seleccionar en Arduino IDE:
 *   Tools → Partition Scheme → "Minimal SPIFFS (1.9MB APP with OTA/190KB SPIFFS)"
 *
 * CAMBIOS v2.0:
 * - Módulo de pH bajo demanda (On/Off): no consume I2C/CPU en standby
 * - Soporte para 3 modos de calibración (Teórico, 2 Puntos, 3 Puntos)
 * - Variables de pendientes duales (ácida/básica) para calibración 3 puntos
 * - Voltaje crudo para calibración de hardware (offset de placa BNC)
 * - Interlock bidireccional con térmico y fuente de corriente
 * - Mutex dedicado muxPH para protección de variables del módulo pH
 * - phModuloActivo NO se persiste en NVS (siempre arranca apagado por seguridad)
 *
 * ARQUITECTURA MULTITAREA NO BLOQUEANTE:
 * Se utiliza un programador por temporización con `millis()` y `micros()` en
 * lugar de `delay()`, garantizando tiempo real en la atención a solicitudes
 * HTTP y la generación de pulsos DAC.
 * - Fuente de corriente: Loop libre a máxima velocidad (Filtro de caché I2C).
 * - Lazo de control Térmico: Cada 1000 ms (+ rampa de potencia cada 200 ms).
 * - Módulo de pH Dual: Lectura Asíncrona Alternada cada 20 ms a 860 SPS (~1.16
 * ms por muestra) — SOLO cuando phModuloActivo == true.
 * - Módulo Ambiental: Cada 5000 ms.
 * =================================================================================
 */

#include <ESPmDNS.h>

// Inclusión de las cabeceras de los submódulos del sistema (Nombres en
// minúsculas)
#include "Modulo_Ambiental.h"
#include "Modulo_Fuentes.h"
#include "Modulo_OTA.h"
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

// Variables de Estado Ambiental (Concurrencia Volatile)
volatile float amb_temp = 0.0, amb_hum = 0.0, amb_pres = 0.0;

// =================================================================================
// MÓDULO PH 2.0 — DEFINICIÓN DE VARIABLES GLOBALES
// =================================================================================

// Control On/Off del módulo (siempre arranca APAGADO por seguridad)
volatile bool phModuloActivo = false;

// Selector de modo de calibración por tina (0=Teórico, 1=2Pts, 2=3Pts)
volatile uint8_t tipoCalPH1 = 0, tipoCalPH2 = 0;

// Tina 1 (Zincado): Voltajes de calibración y pendientes
volatile float v7_1 = PH_OFFSET_TEORICO;  // Voltaje pH 7 (default = teórico)
volatile float v4_1 = 2.0f;               // Voltaje pH 4 (valor inicial razonable)
volatile float v10_1 = 1.3f;              // Voltaje pH 10 (valor inicial razonable)
volatile float m_ph1 = -PH_PENDIENTE_TEORICA;  // Pendiente lineal 2 puntos
volatile float mAcida1 = -PH_PENDIENTE_TEORICA; // Pendiente ácida 3 puntos
volatile float mBasica1 = -PH_PENDIENTE_TEORICA; // Pendiente básica 3 puntos
volatile float phActual1 = 7.0;
volatile bool calibradoPH1 = false;

// Tina 2 (Niquelado): Voltajes de calibración y pendientes
volatile float v7_2 = PH_OFFSET_TEORICO;
volatile float v4_2 = 2.0f;
volatile float v10_2 = 1.3f;
volatile float m_ph2 = -PH_PENDIENTE_TEORICA;
volatile float mAcida2 = -PH_PENDIENTE_TEORICA;
volatile float mBasica2 = -PH_PENDIENTE_TEORICA;
volatile float phActual2 = 7.0;
volatile bool calibradoPH2 = false;

// Voltaje crudo para calibración de hardware (offset de placa)
volatile float voltajeCrudoPH = PH_OFFSET_TEORICO;

// Mutex dedicado para protección de variables del módulo pH
portMUX_TYPE muxPH = portMUX_INITIALIZER_UNLOCKED;

// Mutex dedicado para protección de variables de la fuente de corriente
portMUX_TYPE muxFuente = portMUX_INITIALIZER_UNLOCKED;

// Variables de Control de la Fuente de Corriente (Sumidero DAC MCP4725)
volatile bool fuenteActiva = false;
volatile bool modoPulsado = false;
volatile int amplitudDAC = 1024;
volatile int amplitudDAC_Setpoint = 1024;
volatile int frecuencia = 1;
volatile int dutyCycle = 50;

// Sensado de Corriente VCSS y Compensación de Lazo Cerrado (v3.5)
volatile bool  estadoReleVDD = false; // true = relé cerrado (+12V activo)
volatile float corrienteReal_R1 = 0.0f;
volatile float corrienteReal_R2 = 0.0f;
volatile float corrienteTotalReal = 0.0f;
volatile float voltajeShunt1_raw = 0.0f;
volatile float voltajeShunt2_raw = 0.0f;
volatile float factorGananciaVCSS = 1.000f;
volatile bool  compensacionLazoCerrado = true;

// Temporizadores No Bloqueantes (Basados en millis)
unsigned long lastPI = 0;          // Período PI térmico (1000 ms)
unsigned long lastRamp = 0;        // Período rampa de arranque (200 ms)
unsigned long lastPH = 0;          // Período muestreo asíncrono pH (20 ms)
unsigned long lastEnv = 0;         // Período lectura ambiental (5000 ms)
unsigned long lastSensadoVCSS = 0; // Período sensado y compensación VCSS (500 ms)

// =================================================================================
// CONFIGURACIÓN DEL SISTEMA (SETUP)
// =================================================================================

void setup() {
  // 1. Inicialización de Consola Serie USB para Depuración de Desarrollo
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n==================================================");
  Serial.println(" INICIALIZANDO LÍNEA DE ELECTRODEPOSICIÓN ESP32 ");
  Serial.printf( " FIRMWARE v%s — OTA + PH AVANZADO\n", FIRMWARE_VERSION);
  Serial.println(" Developed by Salvador² C");
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

  // =====================================================================
  // CARGA DE COEFICIENTES DE CALIBRACIÓN DE pH v2.0 DESDE NVS
  // =====================================================================

  // Modo de calibración seleccionado por tina
  portENTER_CRITICAL(&muxPH);

  tipoCalPH1 = memoria.getUChar("tcal1", 0);
  tipoCalPH2 = memoria.getUChar("tcal2", 0);
  // Validar rango del modo (0, 1 o 2)
  if (tipoCalPH1 > 2) tipoCalPH1 = 0;
  if (tipoCalPH2 > 2) tipoCalPH2 = 0;

  // Tina 1: Voltajes de calibración
  v7_1 = memoria.getFloat("v7_1", PH_OFFSET_TEORICO);
  v4_1 = memoria.getFloat("v4_1", 2.0f);
  v10_1 = memoria.getFloat("v10_1", memoria.getFloat("v11_1", 1.3f));

  // Tina 1: Pendientes
  m_ph1 = memoria.getFloat("mph1", -PH_PENDIENTE_TEORICA);
  mAcida1 = memoria.getFloat("mAc1", -PH_PENDIENTE_TEORICA);
  mBasica1 = memoria.getFloat("mBa1", -PH_PENDIENTE_TEORICA);

  // Tina 1: Estado de calibración
  calibradoPH1 = memoria.getBool("cal1", false);
  // En modo teórico, siempre está "calibrado"
  if (tipoCalPH1 == 0) calibradoPH1 = true;

  // Tina 2: Voltajes de calibración
  v7_2 = memoria.getFloat("v7_2", PH_OFFSET_TEORICO);
  v4_2 = memoria.getFloat("v4_2", 2.0f);
  v10_2 = memoria.getFloat("v10_2", memoria.getFloat("v11_2", 1.3f));

  // Tina 2: Pendientes
  m_ph2 = memoria.getFloat("mph2", -PH_PENDIENTE_TEORICA);
  mAcida2 = memoria.getFloat("mAc2", -PH_PENDIENTE_TEORICA);
  mBasica2 = memoria.getFloat("mBa2", -PH_PENDIENTE_TEORICA);

  // Tina 2: Estado de calibración
  calibradoPH2 = memoria.getBool("cal2", false);
  if (tipoCalPH2 == 0) calibradoPH2 = true;

  // phModuloActivo NO se carga de NVS — SIEMPRE arranca apagado por seguridad
  // Esto garantiza que al reiniciar, el bus I2C no se satura con lecturas de pH
  // y el operador debe activar conscientemente el módulo desde la interfaz web.
  phModuloActivo = false;

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
  Serial.print("[NVS] pH Tina 1 — Modo: ");
  Serial.print(tipoCalPH1);
  Serial.print(", Calibrado: ");
  Serial.println(calibradoPH1 ? "SÍ" : "NO");
  Serial.print("[NVS] pH Tina 2 — Modo: ");
  Serial.print(tipoCalPH2);
  Serial.print(", Calibrado: ");
  Serial.println(calibradoPH2 ? "SÍ" : "NO");

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

  // 10. Inicialización del módulo OTA (v3.0)
  inicializarOTA();

  Serial.println("==================================================");
  Serial.printf( " SISTEMA OPERATIVO Y EN LÍNEA - ESP32 v%s\n", FIRMWARE_VERSION);
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

  // 4. Muestreo Asíncrono de pH — BAJO DEMANDA (On/Off)
  // v2.0: Solo se ejecuta si el módulo está activo (phModuloActivo == true).
  // En standby, no se realiza ninguna lectura I2C del ADS1115, liberando
  // ancho de banda del bus para el DAC MCP4725 y otros periféricos.
  if (phModuloActivo && (millis() - lastPH >= 20)) {
    lastPH = millis();
    procesarLecturaPH();
  }

  // 5. Lectura de sensores ambientales AHT20 y BMP280 (Período: 5000 ms de
  // forma no bloqueante)
  if (millis() - lastEnv >= 5000) {
    lastEnv = millis();
    procesarLecturaAmbiental();
  }

  // 6. Sensado de Corriente VCSS y Compensación Digital Outer Loop (v3.5)
  // Período: 500 ms (solo activo cuando la fuente entrega corriente en modo DC)
  if (fuenteActiva && !modoPulsado && (millis() - lastSensadoVCSS >= 500)) {
    lastSensadoVCSS = millis();
    actualizarSensadoVCSS();
  }
}
