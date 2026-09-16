/**
 * =================================================================================
 * TAREA FREERTOS: SUPERVISOR DE SEGURIDAD Y TELEMETRÍA (Task_Supervisor.cpp)
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Implementa el guardián de máxima prioridad del sistema de control industrial (Prio 6).
 * Ejecuta en Core 1 a una cadencia determinista de 20 Hz (periodo de 50 ms).
 *
 * ARQUITECTURA DE SUPERVISIÓN:
 * 1. Watchdog por Software de Tareas (Heartbeat Monitor):
 *    Inspecciona cada 1000 ms que las tareas críticas reporten actividad. Si una tarea
 *    sufre inanición o queda atrapada en un bucle bloqueante, el supervisor detecta
 *    el retraso (> 5000 ms) y activa el protocolo Fail-Safe Latch.
 * 2. Baliza de Diagnóstico Visual (Neopixel RGB):
 *    Genera patrones luminosos distintivos basados en un árbol de decisión de prioridad
 *    estricta. El operador en planta puede discernir el estado físico del equipo
 *    (calentamiento, salida de corriente, pulsado, calibración, reposo o alarma)
 *    a simple vista sin necesidad de abrir la interfaz web.
 * 3. Detección de Hitos de Proceso:
 *    Monitorea cuándo los reactores térmicos alcanzan la consigna con una banda de
 *    tolerancia de +-0.5 °C y emite notificaciones informativas en el log del sistema.
 * =================================================================================
 */

#include "Task_Supervisor.h"
#include "RTOS_Core.h"
#include "Modulo_Termico.h"
#include "Modulo_Fuentes.h"
#include "Modulo_PH.h"
#include "Modulo_OTA.h"
#include "config.h"
#include <math.h>

/**
 * @brief Envía valores de color RGB al LED Neopixel integrado en la placa ESP32-S3.
 *
 * @param r Componente Rojo (0..255).
 * @param g Componente Verde (0..255).
 * @param b Componente Azul (0..255).
 */
static void setVisualLED(uint8_t r, uint8_t g, uint8_t b) {
  #if defined(RGB_BUILTIN) || defined(PIN_LED_RGB)
    neopixelWrite(PIN_LED_RGB, r, g, b);
  #endif
}

static const char* s_estadoLedActual = "standby_beacon";

const char* obtenerEstadoLedActual() {
  return s_estadoLedActual;
}

/**
 * @brief Función principal de la tarea del supervisor (Core 1, Prioridad 6).
 * Bucle infinito temporizado a 50 ms por ciclo.
 */
void taskSupervisorFunc(void *pvParameters) {
  Serial.println("[TASK_SUPERVISOR] Supervisor de seguridad y Baliza LED RGB iniciado en Core 1 (Prioridad 6).");

  // Señal visual de arranque (Blanco tenue durante 300 ms)
  setVisualLED(25, 25, 25);
  vTaskDelay(pdMS_TO_TICKS(300));

  uint32_t ticks = 0;
  float breathAngle = 0.0f;
  uint8_t prevClients = 0xFF;
  bool estabilizadoSP[4] = {false, false, false, false};
  uint32_t lastWarnCurrent = 0;
  uint32_t lastWarnTemp = 0;

  for (;;) {
    // Retardo base de 50 ms para animaciones fluidas (20 cuadros por segundo)
    vTaskDelay(pdMS_TO_TICKS(50));
    ticks++;
    breathAngle += 0.08f;
    if (breathAngle >= 6.283185f) breathAngle = 0.0f; // Periodo de onda sinusoidal ~3.9 segundos

    // =============================================================================
    // 1. EVALUACIÓN DE WATCHDOG DE TAREAS (Cada 1000 ms = 20 ticks)
    // =============================================================================
    // Durante la actualización de firmware OTA se suspende la verificación para evitar
    // falsas alarmas mientras la memoria Flash es borrada y reescrita en bloques de 4KB.
    if (ticks % 20 == 0) {
      if (!isOTAEnProgreso()) {
        checkHeartbeats(5000);
      }
    }

    // =============================================================================
    // 2. MONITOREO DE CLIENTES CONECTADOS AL PUNTO DE ACCESO WI-FI
    // =============================================================================
    uint8_t currClients = WiFi.softAPgetStationNum();
    if (prevClients != 0xFF && currClients != prevClients) {
      if (currClients > prevClients) {
        logSistema(LOG_LVL_INFO, "WIFI", "Dispositivo conectado a SoftAP (Clientes activos: %u)", currClients);
      } else {
        logSistema(LOG_LVL_INFO, "WIFI", "Dispositivo desconectado de SoftAP (Clientes activos: %u)", currClients);
      }
      prevClients = currClients;
    } else if (prevClients == 0xFF) {
      prevClients = currClients;
    }

    // =============================================================================
    // 3. REPORTE PERIÓDICO DE SALUD Y RECURSOS DEL SISTEMA (Cada 60 segundos)
    // =============================================================================
    if (ticks % 1200 == 0) {
      uint32_t upMin = millis() / 60000UL;
      uint32_t heapKb = ESP.getFreeHeap() / 1024;
      float psramMb = (float)ESP.getFreePsram() / (1024.0f * 1024.0f);
      logSistema(LOG_LVL_INFO, "SYS", "Salud: Uptime %lum | Heap: %uKB | PSRAM: %.1fMB | WiFi: %u cli",
                 (unsigned long)upMin, heapKb, psramMb, currClients);
    }

    // =============================================================================
    // 4. MÁQUINA DE ESTADOS Y CONTROL DE BALIZA VISUAL RGB (ISA-18.2)
    // =============================================================================
    if (g_failsafe_latched) {
      // Reasegurar físicamente el corte de potencia en cada ciclo de alarma
      digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
      Serial2.println("0,0,0,0");

      bool esPeligroCritico = (g_failsafe_code == ERR_TEMP_OVERHEAT || 
                               g_failsafe_code == ERR_VCSS_OVERCURRENT || 
                               g_failsafe_code == ERR_RTOS_HEARTBEAT);

      if (esPeligroCritico) {
        // 🔴 Prioridad 0: Peligro Físico Crítico (Estroboscópico violento a 4 Hz, 100ms ON / 100ms OFF)
        s_estadoLedActual = "critical";
        bool strobe = ((ticks / 2) % 2 == 0);
        setVisualLED(strobe ? 120 : 0, 0, 0);
      } else {
        // 🔴 Prioridad 1: Falla de Sensor o Pérdida de Enlace (Parpadeo Lento a 1 Hz, 500ms ON / 500ms OFF)
        s_estadoLedActual = "fault";
        bool blink = ((ticks / 10) % 2 == 0);
        setVisualLED(blink ? 65 : 0, 0, 0);
      }
    } else if (isOTAEnProgreso()) {
      // ⚪ Prioridad 2: Actualización de Firmware OTA en Curso (Parpadeo Rápido 10 Hz en Blanco)
      s_estadoLedActual = "ota";
      bool otaBlink = ((ticks / 2) % 2 == 0);
      setVisualLED(otaBlink ? 75 : 0, otaBlink ? 75 : 0, otaBlink ? 75 : 0);
    } else {
      // Snapshot atómico de variables de operación bajo xDataMutex
      bool calentando = false;
      bool fuenteOn = false;
      bool phOn = false;
      bool pulsado = false;
      bool algunTermoparDetectado = false;

      if (takeDataMutex(pdMS_TO_TICKS(10))) {
        for (int i = 0; i < 4; i++) {
          if (canales[i].activo) calentando = true;
          if (canales[i].temperatura > 0.0f && canales[i].temperatura < 150.0f) {
            algunTermoparDetectado = true;
          }
        }
        fuenteOn = fuenteActiva;
        pulsado = modoPulsado;
        phOn = phModuloActivo;
        giveDataMutex();
      }

      // Hito: Detección de estabilización térmica en consigna (+-0.5 °C)
      for (int i = 0; i < 4; i++) {
        if (canales[i].activo) {
          float errT = fabs(canales[i].temperatura - canales[i].setpoint);
          if (errT <= 0.5f && !estabilizadoSP[i]) {
            estabilizadoSP[i] = true;
            const char* nomb[] = {"Limpieza", "Decapado", "Celda Hull", "Niquelado"};
            logSistema(LOG_LVL_INFO, "TERMICO", "Canal %d (%s) en consigna de %.1f C (Estabilizado)",
                       i, nomb[i], canales[i].setpoint);
          }
        } else {
          estabilizadoSP[i] = false;
        }
      }

      // Advertencias preventivas en log de telemetría
      if (fuenteOn && corrienteTotalReal > 3.0f && (millis() - lastWarnCurrent > 15000)) {
        lastWarnCurrent = millis();
        logSistema(LOG_LVL_WARN, "VCSS", "Corriente elevada: %.2f A (Limite: 3.50 A)", corrienteTotalReal);
      }

      for (int i = 0; i < 4; i++) {
        if (canales[i].activo && canales[i].temperatura > (canales[i].setpoint + 3.0f) && (millis() - lastWarnTemp > 15000)) {
          lastWarnTemp = millis();
          logSistema(LOG_LVL_WARN, "TERMICO", "Canal %d cerca a sobretemp: %.1f C (SP: %.1f C)",
                     i, canales[i].temperatura, canales[i].setpoint);
        }
      }

      // Resumen periódico de proceso activo cada 30 segundos (600 ticks)
      if (ticks % 600 == 0 && (calentando || fuenteOn || phOn)) {
        char fStr[24] = "OFF";
        if (fuenteOn) {
          snprintf(fStr, sizeof(fStr), "%.2fA (%s)", corrienteTotalReal, pulsado ? "Pulsado" : "DC");
        }
        logSistema(LOG_LVL_INFO, "PROCESO", "T:[%.1f,%.1f,%.1f,%.1f]C | VCSS:%s | pH:%.2f",
                   canales[0].temperatura, canales[1].temperatura, canales[2].temperatura, canales[3].temperatura,
                   fStr, phActual);
      }

      // Árbol de Estados Operativos para la Baliza Neopixel:
      if (!algunTermoparDetectado && !isADSConectado() && (bool)Serial) {
        // 🟣 Prioridad 3: Modo Banco de Pruebas USB (Sin planta de potencia conectada)
        s_estadoLedActual = "testbench";
        float factor = 0.20f + 0.80f * (0.5f * (1.0f + sinf(breathAngle)));
        setVisualLED((uint8_t)(45.0f * factor), 0, (uint8_t)(75.0f * factor));
      } else if (phOn) {
        // 💖 Prioridad 4: Calibración / Modo Lectura de pH (Fucsia Neón con respiración suave)
        s_estadoLedActual = "ph";
        float fucsiaBreath = 0.35f + 0.65f * (0.5f * (1.0f + sinf(breathAngle * 2.0f)));
        setVisualLED((uint8_t)(70.0f * fucsiaBreath), 0, (uint8_t)(45.0f * fucsiaBreath));
      } else if (calentando && fuenteOn) {
        // ⚡ Prioridad 5A: Calentamiento Térmico (450W) + Fuente VCSS Simultáneos
        s_estadoLedActual = pulsado ? "term_pulse" : "term_dc";
        if (pulsado) {
          // Térmico + Pulsado: Base Azul Cobalto continuo + Pulsos Cian Eléctrico brillante
          bool pulsoOn = ((ticks / 3) % 2 == 0);
          if (pulsoOn) {
            setVisualLED(25, 80, 100); // Pico de pulso de corriente
          } else {
            setVisualLED(0, 20, 60);   // Valle continuo de calentamiento
          }
        } else {
          // Térmico + Salida de Corriente Continua (DC): Cian Eléctrico Sólido y Estable
          setVisualLED(15, 65, 85);
        }
      } else if (calentando) {
        // 🔵 Prioridad 5B: Solo Calentamiento Térmico Activo (Azul Cobalto Profundo continuo)
        s_estadoLedActual = "term_only";
        setVisualLED(0, 15, 90);
      } else if (fuenteOn) {
        s_estadoLedActual = pulsado ? "pulse_only" : "dc_only";
        if (pulsado) {
          // ⚡ Prioridad 5C: Solo Salida de Corriente en MODO PULSADO (Azul Eléctrico alternante)
          bool pulsoOn = ((ticks / 3) % 2 == 0);
          setVisualLED(pulsoOn ? 10 : 0, pulsoOn ? 55 : 5, pulsoOn ? 90 : 15);
        } else {
          // 💎 Prioridad 5D: Solo Salida de Corriente en MODO CONTINUO / DC (Azul Celeste fijo)
          setVisualLED(0, 60, 80);
        }
      } else if (!ahtInicializado && !bmpInicializado) {
        // 🟡 Prioridad 6: Alerta Menor / Advertencia (Sensores meteorológicos ausentes, modo degradado)
        s_estadoLedActual = "env_missing";
        setVisualLED(45, 30, 0);
      } else if (WiFi.softAPgetStationNum() > 0) {
        // 🟢 Prioridad 7: Sistema Operativo, Conectado por Interfaz Web, Sin Cargas Activas (Standby)
        s_estadoLedActual = "standby_connected";
        float beat = 0.85f + 0.15f * (0.5f * (1.0f + sinf(breathAngle)));
        setVisualLED(0, (uint8_t)(60.0f * beat), (uint8_t)(15.0f * beat));
      } else {
        // 🟢 Prioridad 8: Sistema Operativo, Esperando Conexión Wi-Fi SoftAP "Uli" (Faro verde cada 2.5s)
        s_estadoLedActual = "standby_beacon";
        bool destelloFaro = (ticks % 50 < 3); // 150 ms destello cada 2500 ms
        if (destelloFaro) {
          setVisualLED(0, 65, 20); // Destello verde brillante
        } else {
          setVisualLED(0, 4, 1);   // Verde tenue de presencia en reposo
        }
      }
    }
  }
}

/**
 * @brief Instancia la tarea en FreeRTOS ligada a Core 1 con prioridad 6 y stack de 3584 bytes.
 */
void iniciarTaskSupervisor() {
  xTaskCreatePinnedToCore(
      taskSupervisorFunc,
      "Task_Supervisor",
      STACK_TASK_SUPERVISOR,
      NULL,
      PRIO_TASK_SUPERVISOR,
      &hTaskSupervisor,
      CORE_REALTIME
  );
}

