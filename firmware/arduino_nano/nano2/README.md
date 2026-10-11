# Firmware de Potencia AC: Nano2 (Tiempo Proporcional / Burst Firing)

## 📌 Rol en el Sistema
Este es el **firmware activo de producción** para el microcontrolador esclavo **Arduino Nano (ATmega328P @ 16 MHz)** conectado a la **placa de TRIACs de fabricación propia** del laboratorio.

Gobernado por la librería `JELDimmer2`, modula la potencia térmica suministrada a:
- **Tina 1 (Canal 0):** Resistencia de inmersión 450 W — Desengrase Alcalino (85–90 °C)
- **Tina 2 (Canal 1):** Resistencia de inmersión 450 W — Decapado Alcalino (85–90 °C)
- **Tina 3 (Canal 2):** Resistencia de cartucho 18 W — Celda Hull de 267 mL (25 °C / 40 °C)
- **Tina 4 (Canal 3):** Resistencia de inmersión 450 W — Niquelado sobre Zinc (30–35 °C)

---

## ⚡ Principio de Operación: Tiempo Proporcional (Burst Firing)
A diferencia del recorte de ángulo de fase convencional, este módulo utiliza **modulación por tiempo proporcional (Burst Firing por software)** en ventanas temporales fijas de **3000 ms**:
- Modula el ciclo de trabajo por tramos enteros dentro de la ventana de 3 segundos (ej. 50% = 1.5 s encendido, 1.5 s apagado).
- **Aclaración de hardware:** La etapa utiliza optoacopladores MOC3021 (fase aleatoria). El pin **D3 (ZC_PIN)** está reservado en hardware para futura sincronización por interrupción en cruce por cero en banco de pruebas (S11).

---

## 🔒 Mecanismos de Seguridad
1. **Watchdog de Hardware AVR (`wdt_enable(WDTO_1S)`):**
   Supervisa el lazo principal a 1000 ms. Si ocurre un bloqueo de ejecución, reinicia el microcontrolador y fuerza las compuertas a nivel BAJO (LOW).
2. **Perro Guardián UART (`TIMEOUT_UART_MS = 4000 ms`):**
   Si el ESP32 deja de enviar la trama serie periódica `p0,p1,p2,p3\n` por más de 4 segundos, todas las potencias se ponen en 0% y las compuertas se apagan inmediatamente.
3. **Arranque Seguro en LOW:** Todos los pines de compuerta (`GATE_PINS`) se configuran inmediatamente como `OUTPUT, LOW` en `setup()` antes de cualquier otra instrucción.

---

## 🔌 Asignación de Pines
- **Pin D3 (INT1):** Detección de Cruce por Cero (`ZC_PIN`) con pull-up interno.
- **Pines D7, D8, D9, D10:** Compuertas de disparo de los 4 canales de potencia (`GATE_PINS`).
- **UART (Pin D0 / RX):** Recepción de tramas serie a 9600 bps desde el ESP32-S3 (`PIN_UART2_TX` = GPIO 17).
