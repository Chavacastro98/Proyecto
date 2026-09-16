/**
 * =================================================================================
 * NÚCLEO DEL SISTEMA OPERATIVO EN TIEMPO REAL (RTOS_Core.cpp)
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 * Sistema Operativo: FreeRTOS SMP (Symmetric Multiprocessing)
 *
 * PROPÓSITO TÉCNICO:
 * Este módulo centraliza las primitivas de sincronización, la gestión de memoria
 * compartida entre núcleos (Cores 0 y 1), la jerarquía de semáforos/mutexes, el
 * buffer circular de telemetría y el lazo de seguridad "Fail-Safe Latch".
 *
 * ARQUITECTURA DE SINCRONIZACIÓN Y PROTECCIÓN CONTRA DEADLOCKS:
 * 1. xI2CMutex:   Serializa el acceso a la línea SDA/SCL (GPIO 8 / GPIO 9).
 *                 Compartido por ADS1115 (pH/shunts), MCP4725 (DAC), AHT20 y BMP280.
 * 2. xSPIMutex:   Serializa las lecturas de los 4 amplificadores de termopar MAX6675.
 * 3. xDataMutex:  Protege las estructuras de datos globales que cruzan la frontera
 *                 entre Core 0 (Comunicaciones/Web) y Core 1 (Tiempo Real).
 * 4. xLogMutex:   Garantiza inserción atómica en el buffer circular de logs en RAM.
 *
 * FILOSOFÍA DE SEGURIDAD INDUSTRIAL (FAIL-SAFE LATCH):
 * Ante cualquier fallo crítico (desconexión de sensor, sobrecorriente, sobrecalentamiento
 * o congelamiento de tarea por watchdog), el sistema entra en modo enclavado ("latch"),
 * ejecutando una secuencia determinista en cascada para llevar la planta física
 * a un estado pasivo y energéticamente seguro (0V / 0A / Relé abierto / TRIACs apagados).
 * =================================================================================
 */

#include "RTOS_Core.h"
#include "Modulo_Fuentes.h"
#include <string.h>
#include <stdarg.h>
#include <stdio.h>

// =================================================================================
// INSTANCIACIÓN DE PRIMITIVAS FREERTOS Y HANDLES DE TAREAS
// =================================================================================

/** @brief Mutex binario para el arbitraje exclusivo del bus I2C (Wire) */
SemaphoreHandle_t xI2CMutex   = NULL;

/** @brief Mutex binario para el bus SPI compartido por los módulos MAX6675 */
SemaphoreHandle_t xSPIMutex   = NULL;

/** @brief Mutex de protección para las variables y estructuras volátiles globales */
SemaphoreHandle_t xDataMutex  = NULL;

/** @brief Mutex interno que protege el ring-buffer de eventos y logs en memoria RAM */
static SemaphoreHandle_t xLogMutex = NULL;

/** @brief Handles de control para introspección y monitoreo de tareas FreeRTOS */
TaskHandle_t hTaskSupervisor  = NULL;
TaskHandle_t hTaskTermico     = NULL;
TaskHandle_t hTaskFuente      = NULL;
TaskHandle_t hTaskSensado     = NULL;
TaskHandle_t hTaskWeb         = NULL;

// =================================================================================
// VARIABLES DE ESTADO FAIL-SAFE (SEGURIDAD ENCLAVADA)
// =================================================================================

/**
 * @brief Bandera enclavada de seguridad.
 * Si es true, inhabilita de inmediato cualquier activación de fuente o calentamiento.
 * Solo puede ser restablecida manualmente por el operador tras corregir la causa raíz.
 */
volatile bool g_failsafe_latched = false;

/** @brief Código numérico ISA-18.2 que identifica la causa exacta de la alarma */
volatile uint8_t g_failsafe_code = ERR_NONE;

/** @brief Cadena descriptiva que detalla el evento generador del enclavamiento */
char g_failsafe_reason[64] = "OK";

// =================================================================================
// ARREGLO DE WATCHDOG POR SOFTWARE (HEARTBEAT MONITOR)
// =================================================================================

/**
 * @brief Timestamps (millis) de la última confirmación de actividad por tarea.
 * Permite detectar si una tarea de menor prioridad quedó bloqueada indefinidamente
 * por contención de recursos, starvation o un bucle no balanceado.
 */
static volatile uint32_t s_heartbeats[HB_COUNT] = {0, 0, 0, 0};

/** @brief Nombres legibles de las tareas para reporte de diagnóstico */
static const char* s_taskNames[HB_COUNT] = {"Termico", "Fuente", "Sensado", "Web"};

// =================================================================================
// BUFFER CIRCULAR (RING BUFFER) DE EVENTOS Y LOGS EN RAM
// =================================================================================

/** @brief Almacenamiento estático de registros para evitar fragmentación del heap */
static LogEntry s_logRing[MAX_LOG_ENTRIES];

/** @brief Puntero al índice del próximo elemento a escribir en el buffer circular */
static uint16_t s_logHead = 0;

/** @brief Cantidad de entradas activas acumuladas en el buffer circular (máx. 64) */
static uint16_t s_logCount = 0;

// =================================================================================
// INICIALIZACIÓN DEL NÚCLEO RTOS
// =================================================================================

/**
 * @brief Crea los mutexes de hardware/datos e inicializa el subsistema de telemetría.
 * Debe ser invocada en setup() ANTES de inicializar cualquier módulo dependiente.
 */
void rtosInicializarNucleo() {
  Serial.println("[RTOS_CORE] Creando primitivas de sincronización...");

  if (xI2CMutex == NULL)  xI2CMutex  = xSemaphoreCreateMutex();
  if (xSPIMutex == NULL)  xSPIMutex  = xSemaphoreCreateMutex();
  if (xDataMutex == NULL) xDataMutex = xSemaphoreCreateMutex();
  if (xLogMutex == NULL)  xLogMutex  = xSemaphoreCreateMutex();

  uint32_t now = millis();
  for (int i = 0; i < HB_COUNT; i++) {
    s_heartbeats[i] = now;
  }

  logSistema(LOG_LVL_INFO, "CORE", "Nucleo FreeRTOS y RingBuffer de logs inicializados.");
}

// =================================================================================
// GESTORES ENVOLVENTES (WRAPPERS) DE MUTEXES CON TIEMPO DE ESPERA ACOTADO
// =================================================================================

/**
 * @brief Intenta tomar el control exclusivo del bus I2C.
 * @param xTicksToWait Tiempo límite en ticks de FreeRTOS antes de desistir.
 * @return true si se obtuvo el mutex; false en caso de contención/timeout.
 */
bool takeI2CMutex(TickType_t xTicksToWait) {
  if (xI2CMutex == NULL) return false;
  return (xSemaphoreTake(xI2CMutex, xTicksToWait) == pdTRUE);
}

/**
 * @brief Libera el bus I2C para que otra tarea pueda utilizarlo.
 */
void giveI2CMutex() {
  if (xI2CMutex != NULL) {
    xSemaphoreGive(xI2CMutex);
  }
}

/**
 * @brief Intenta tomar el control exclusivo del bus SPI (MAX6675).
 * @param xTicksToWait Tiempo límite en ticks antes de desistir.
 * @return true si se obtuvo el mutex; false en caso de timeout.
 */
bool takeSPIMutex(TickType_t xTicksToWait) {
  if (xSPIMutex == NULL) return false;
  return (xSemaphoreTake(xSPIMutex, xTicksToWait) == pdTRUE);
}

/**
 * @brief Libera el bus SPI.
 */
void giveSPIMutex() {
  if (xSPIMutex != NULL) {
    xSemaphoreGive(xSPIMutex);
  }
}

/**
 * @brief Intenta adquirir el cerrojo de los datos volátiles del sistema.
 * @param xTicksToWait Tiempo límite en ticks antes de desistir.
 * @return true si los datos están asegurados para lectura/escritura atómica.
 */
bool takeDataMutex(TickType_t xTicksToWait) {
  if (xDataMutex == NULL) return false;
  return (xSemaphoreTake(xDataMutex, xTicksToWait) == pdTRUE);
}

/**
 * @brief Libera el cerrojo de datos del sistema.
 */
void giveDataMutex() {
  if (xDataMutex != NULL) {
    xSemaphoreGive(xDataMutex);
  }
}

// =================================================================================
// SUBSISTEMA DE LOGGING ATÓMICO Y BUFFER CIRCULAR EN RAM
// =================================================================================

/**
 * @brief Registra un mensaje formateado tanto en la consola Serial como en el buffer RAM.
 * Diseñado con búfer local en pila para asegurar reentrancia y evitar asignaciones dinámicas.
 *
 * @param level Nivel de severidad (LOG_LVL_INFO, LOG_LVL_WARN, LOG_LVL_ERR).
 * @param tag Etiqueta identificadora del subsistema emisor (ej. "CORE", "VCSS", "WIFI").
 * @param fmt Cadena de formato tipo printf.
 */
void logSistema(uint8_t level, const char* tag, const char* fmt, ...) {
  char buf[80];
  va_list args;
  va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args);
  va_end(args);

  const char* lvlStr = "INFO";
  if (level == LOG_LVL_WARN) lvlStr = "WARN";
  else if (level == LOG_LVL_ERR) lvlStr = "ERR";

  // 1. Salida directa e inmediata por el puerto USB Serial CDC
  Serial.printf("[%lu][%s][%s] %s\n", (unsigned long)millis(), lvlStr, tag ? tag : "SYS", buf);

  // 2. Inserción protegida en el RingBuffer de memoria RAM
  // Se emplea un timeout estricto de 10 ms para evitar que la traza degrade tareas críticas
  if (xLogMutex != NULL && xSemaphoreTake(xLogMutex, pdMS_TO_TICKS(10)) == pdTRUE) {
    LogEntry &entry = s_logRing[s_logHead];
    entry.timestampMs = millis();
    entry.level = level;
    if (tag) {
      strncpy(entry.tag, tag, sizeof(entry.tag) - 1);
      entry.tag[sizeof(entry.tag) - 1] = '\0';
    } else {
      strcpy(entry.tag, "SYS");
    }
    strncpy(entry.message, buf, sizeof(entry.message) - 1);
    entry.message[sizeof(entry.message) - 1] = '\0';

    // Aritmética modular del puntero de cabeza
    s_logHead = (s_logHead + 1) % MAX_LOG_ENTRIES;
    if (s_logCount < MAX_LOG_ENTRIES) s_logCount++;

    xSemaphoreGive(xLogMutex);
  }
}

/**
 * @brief Serializa el contenido del buffer circular en un arreglo JSON para la interfaz web.
 * Realiza un recorrido cronológico desde la entrada más antigua hasta la más reciente.
 *
 * @param buffer Puntero al búfer de caracteres de destino.
 * @param maxLen Capacidad máxima en bytes del búfer provisto.
 */
void obtenerLogsJSON(char* buffer, size_t maxLen) {
  if (buffer == NULL || maxLen < 16) return;

  int offset = 0;
  offset += snprintf(buffer + offset, maxLen - offset, "[");

  if (xLogMutex != NULL && xSemaphoreTake(xLogMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
    uint16_t startIdx = 0;
    // Si el buffer ya dio la vuelta completa, el registro más antiguo reside en s_logHead
    if (s_logCount == MAX_LOG_ENTRIES) {
      startIdx = s_logHead;
    }

    for (uint16_t i = 0; i < s_logCount; i++) {
      uint16_t idx = (startIdx + i) % MAX_LOG_ENTRIES;
      const LogEntry &e = s_logRing[idx];

      int written = snprintf(buffer + offset, maxLen - offset,
                             "{\"t\":%lu,\"lvl\":%d,\"tag\":\"%s\",\"msg\":\"%s\"}%s",
                             (unsigned long)e.timestampMs, (int)e.level, e.tag, e.message,
                             (i < s_logCount - 1) ? "," : "");
      if (written < 0 || (size_t)(offset + written) >= maxLen - 4) {
        break; // Salvaguarda física contra desbordamiento de búfer
      }
      offset += written;
    }
    xSemaphoreGive(xLogMutex);
  }

  snprintf(buffer + offset, maxLen - offset, "]");
}

// =================================================================================
// GESTIÓN DE SEGURIDAD INDUSTRIAL: FAIL-SAFE LATCH
// =================================================================================

/**
 * @brief Dispara el protocolo de parada de emergencia enclavada (Fail-Safe Latch).
 *
 * PROTOCOLO DE DESCONEXIÓN EN CASCADA:
 * Paso 1: Desenergización instantánea del relé de potencia VCSS (GPIO 20) para aislar +12V.
 * Paso 2: Envío inmediato de la trama "0,0,0,0\n" al Arduino Nano vía UART2 para apagar
 *         los 4 TRIACs de calentamiento térmico (450W).
 * Paso 3: Forzado del DAC MCP4725 a 0V mediante un intento de toma rápida de mutex I2C.
 * Paso 4: Puesta a cero de todas las consignas lógicas bajo cerrojo de datos (xDataMutex).
 *
 * @param errCode Código identificador del fallo (enum ErrorSistema).
 * @param reason Explicación legible del motivo de la parada.
 */
void triggerFailSafe(uint8_t errCode, const char* reason) {
  // Enclavamiento inmediato de bandera volátil para bloquear lazos de control
  g_failsafe_latched = true;
  g_failsafe_code = errCode;
  if (reason != NULL) {
    strncpy(g_failsafe_reason, reason, sizeof(g_failsafe_reason) - 1);
    g_failsafe_reason[sizeof(g_failsafe_reason) - 1] = '\0';
  }

  logSistema(LOG_LVL_ERR, "FAILSAFE", "Latch activado (Cod: %d) - %s", errCode, g_failsafe_reason);

  // 1. Apagado prioritario de consigna analógica DAC a 0V (ZCS - Zero Current Switching)
  // El corte por compuertas MOSFET es casi instantáneo (<50 us) y suprime la corriente
  // antes de la apertura mecánica, protegiendo los contactos del relé de arcos inductivos.
  if (isDACInicializado() && takeI2CMutex(pdMS_TO_TICKS(20))) {
    dac.setVoltage(0, false);
    giveI2CMutex();
  }

  // 2. Desconexión física galvánica del relé VCSS (+12V aislado con corriente = 0A)
  digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
  estadoReleVDD = false;

  // 3. Apagado inmediato de TRIACs térmicos en Arduino Nano esclavo
  Serial2.println("0,0,0,0");

  // 4. Apagar banderas de actuación bajo cerrojo de datos
  if (takeDataMutex(pdMS_TO_TICKS(50))) {
    fuenteActiva = false;
    amplitudDAC = 0;
    giveDataMutex();
  }
}

/**
 * @brief Sobrecarga de conveniencia que clasifica el fallo como error de watchdog.
 * @param reason Motivo textual del enclavamiento.
 */
void triggerFailSafe(const char* reason) {
  triggerFailSafe(ERR_RTOS_HEARTBEAT, reason);
}

/**
 * @brief Restablece la condición de Fail-Safe Latch tras validación del operador.
 * Requiere que la condición física generadora de la alarma haya sido eliminada.
 */
void clearFailSafe() {
  if (takeDataMutex(pdMS_TO_TICKS(50))) {
    g_failsafe_latched = false;
    g_failsafe_code = ERR_NONE;
    strncpy(g_failsafe_reason, "OK", sizeof(g_failsafe_reason));
    giveDataMutex();
    logSistema(LOG_LVL_INFO, "FAILSAFE", "Alarma Fail-Safe restablecida por el operador.");
  }
}

// =================================================================================
// SUPERVISIÓN DE HEARTBEAT (WATCHDOG ENTRE TAREAS)
// =================================================================================

/**
 * @brief Registra la actividad periódica de una tarea específica.
 * Invocado internamente por cada tarea al completar un ciclo de trabajo exitoso.
 *
 * @param taskId Índice de la tarea (HB_ID_TERMICO, HB_ID_FUENTE, etc.).
 */
void feedHeartbeat(uint8_t taskId) {
  if (taskId < HB_COUNT) {
    s_heartbeats[taskId] = millis();
  }
}

/**
 * @brief Evalúa la salud temporal de todas las tareas registradas.
 * Invocado por Task_Supervisor a intervalos regulares (1 Hz). Si alguna tarea
 * supera el tiempo máximo de inactividad, activa automáticamente el Fail-Safe Latch.
 *
 * @param maxInactivityMs Límite de inactividad tolerado en milisegundos (típicamente 5000 ms).
 * @return true si todas las tareas están respondiendo; false si se detectó inanición.
 */
bool checkHeartbeats(uint32_t maxInactivityMs) {
  uint32_t now = millis();
  for (int i = 0; i < HB_COUNT; i++) {
    if ((now - s_heartbeats[i]) > maxInactivityMs) {
      char err[64];
      snprintf(err, sizeof(err), "Inactividad en Task_%s (>%u ms)", s_taskNames[i], maxInactivityMs);
      triggerFailSafe(ERR_RTOS_HEARTBEAT, err);
      return false;
    }
  }
  return true;
}

// =================================================================================
// UTILIDADES AUXILIARES DE FORMATEO
// =================================================================================

/**
 * @brief Escapa comillas dobles y barras diagonales inversas para cadenas JSON seguras.
 * Previene corrupción de sintaxis JSON originada por caracteres especiales en mensajes.
 *
 * @param src Cadena de origen.
 * @param dst Búfer de destino para la cadena escapada.
 * @param maxLen Longitud máxima del búfer de destino.
 */
void escaparJSON(const char* src, char* dst, size_t maxLen) {
  if (!src || !dst || maxLen == 0) return;
  size_t j = 0;
  for (size_t i = 0; src[i] && j < maxLen - 1; i++) {
    if (src[i] == '"' || src[i] == '\\') {
      if (j < maxLen - 2) {
        dst[j++] = '\\';
      }
    }
    dst[j++] = src[i];
  }
  dst[j] = '\0';
}

