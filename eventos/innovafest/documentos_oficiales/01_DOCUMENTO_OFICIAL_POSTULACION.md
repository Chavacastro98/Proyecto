# EXPEDIENTE TÉCNICO DE POSTULACIÓN
## CONVOCATORIA OFICIAL DE INNOVACIÓN TECNOLÓGICA — PREMIO A LA INNOVACIÓN MEXICANA

---

### PORTADA DEL PROYECTO

**Título del Proyecto:**  
**ELECTRODO-32: Equipo de Laboratorio para Experimentación y Control en Tiempo Real con Obtención de Datos Operativos (Planta Piloto de Electrodeposición)**

**Modalidad de Participación:**  
En equipo multidisciplinario (Estudiantes de Educación Superior).

**Integrantes del Equipo Ejecutor (Alumnos Postulantes):**
1. **Salvador Castro Pérez** (Representante del Equipo) — Estudiante de Ingeniería en Comunicaciones y Electrónica, CUCEI, Universidad de Guadalajara. Contacto: salva.castro@alumnos.udg.mx / Guadalajara, Jalisco.
2. **Fernando Salvador Samayoa Martínez** — Estudiante de Ingeniería en Comunicaciones y Electrónica, CUCEI, Universidad de Guadalajara.
3. **Víctor Ulises Gutiérrez Ramírez** — Estudiante de Ingeniería Química, CUCEI, Universidad de Guadalajara.

**Asesores Científicos y Contexto de Investigación Aplicada:**
* **Dr. Omar Alejandro González-Meza** — Profesor Investigador, CUCEI, Universidad de Guadalajara.
* **Dr. Norberto Casillas Santana** — Profesor Investigador, CUCEI, Universidad de Guadalajara.
* **Caso de Estudio de Referencia Industrial:** Problemática técnica de adherencia identificada en el sector de acabados superficiales de Guadalajara (referencia detonadora: *Volta Plating Solutions*).

**Eje Temático y Categoría:**  
* **Desafío Nacional:** Categoría 6: Transformación Digital e Inteligencia Artificial (Industria 4.0 / Manufactura Inteligente).  
*(Compatible con Desafío Regional Guadalajara — Categoría 1: Economía Digital y TI / Innovaciones en Diseño de Hardware).*

**Pregunta Detonadora a Resolver:**  
*¿Cómo se puede mejorar con tecnologías modernas un proceso que ha sido empírico o de seguimiento de recetas durante años, como la electrodeposición, y facilitar la experimentación o validación de estos mismos métodos empíricos siguiendo tendencias como la Industria 4.0?*

---

### 1. NECESIDAD POR RESOLVER Y CONTEXTO

#### 1.1 El Problema Industrial y el Empirismo en la Galvanoplastia
El aluminio y sus aleaciones estructurales (particularmente el aluminio 6061-T6, ampliamente utilizado en los sectores aeroespacial, automotriz, electrónico y metalmecánico de la región occidente de México) poseen una relación resistencia-peso excepcional. Sin embargo, su aprovechamiento integral requiere recubrimientos superficiales galvánicos (como zincado y niquelado electrolítico) para dotarlo de resistencia al desgaste, conductividad superficial y protección contra la corrosión.

Históricamente, la electrodeposición en talleres y laboratorios pequeños ha operado como un oficio empírico basado en el seguimiento estático de recetas tradicionales. Sin embargo, sobre sustratos de aluminio el proceso físico-químico es altamente sensible: al contacto con el aire se forma instantáneamente una película pasivante de alúmina (Al₂O₃) que impide la adherencia metalúrgica. Superar esta barrera exige secuencias precisas de Desengrase Alcalino (80–95 °C), Decapado/Activación (80–95 °C) y Deposición de Zinc previa al niquelado, donde cualquier desviación térmica, eléctrica o de pH invalida tanto la producción como la experimentación.

#### 1.2 Contexto Industrial y Caso de Estudio Detonador
A partir de una problemática real de la industria local de recubrimientos compartida con el cuerpo académico de CUCEI —tomando como caso de estudio de referencia las dificultades técnicas reportadas en talleres como **Volta Plating Solutions**— se identificó que los recubrimientos de níquel sobre aluminio presentan fallas recurrentes:
* **Falta de adherencia metalúrgica y acabado opaco/quebradizo:** Desprendimiento de la película ante esfuerzos mecánicos (no superando pruebas de cinta ASTM D3359).
* **Causa raíz identificada:** La dependencia de métodos empíricos sin control electrónico repetible: variaciones térmicas severas en el pretratamiento, deriva de pH y la inyección de corriente continua descontrolada durante la electrodeposición en Celda Hull, dificultando además experimentar y validar sistemáticamente mejoras a la receta química.

#### 1.3 Soluciones Existentes y Brecha Tecnológica
Actualmente, las opciones en el mercado mexicano presentan dos extremos inviables para talleres locales y laboratorios de experimentación:
1. **Operación artesanal / empírica:** Reguladores analógicos ruidosos, calentamiento manual sin lazo cerrado, lecturas esporádicas con tiras reactivas y fuentes de laboratorio convencionales sin modulación ni registro de datos. Resultado: nula reproducibilidad experimental, riesgo térmico y desperdicio de reactivos.
2. **Maquinaria industrial importada (Atotech/Schlötter):** Líneas automatizadas con costos de $80,000 a $250,000 USD, basadas en PLCs y licencias propietarias cerradas, inaccesibles para MiPyMEs o laboratorios universitarios.

Existe una clara oportunidad tecnológica: demostrar que es posible modernizar procesos químicos tradicionales hacia la **Industria 4.0** combinando **microcontroladores (MCUs) de bajo costo, módulos comerciales prefabricados y electrónica de potencia propia**, apoyándose en la **Inteligencia Artificial generativa** para acelerar la programación de interfaces Web y sistemas SCADA.

---

### 2. DESCRIPCIÓN DE LA PROPUESTA DE VALOR

#### 2.1 En qué Consiste la Solución
Se diseñó, construyó y validó una **Planta Piloto Automatizada de Tratamiento Químico y Celda Hull (267 mL)** basada en una arquitectura distribuida de **MCUs de bajo costo, módulos comerciales prefabricados, electrónica analógica/potencia dedicada y supervisión SCADA / Web**. La planta automatiza y parametriza 4 etapas:
1. **Etapa 1 — Desengrase Alcalino (85–90 °C, 240 s):** Remoción termoquímica superficial (Na₃PO₄ + Na₂SiO₃ + PEG-400).
2. **Etapa 2 — Decapado y Activación (85–90 °C, 120 s):** Remoción controlada de la película pasivante de Al₂O₃.
3. **Etapa 3 — Zincado en Celda Hull normalizada (267 mL, 25 °C o 40 °C, 1.50 A):** Deposición de zinc en corriente continua (DC) o corriente pulsada (10 Hz, 20% ciclo de trabajo) para evaluar experimentalmente el gradiente de densidad de corriente sobre la probeta.
4. **Etapa 4 — Niquelado Electrolítico Watts (30–40 °C, 600 s):** Recubrimiento protector y decorativo de níquel.

#### 2.2 Componentes de Ingeniería e Integración con Inteligencia Artificial
* **Modernización con MCUs de Bajo Costo y Módulos Comerciales Prefabricados:**
  * **Controlador Principal (ESP32-S3 Dual-Core @ 240 MHz):** MCU de bajo costo y altas prestaciones que ejecuta FreeRTOS con 7 tareas concurrentes, integrando módulos comerciales prefabricados por bus SPI/I2C (acondicionadores de termopar **MAX6675**, convertidor digital-analógico **MCP4725** de 12 bits y módulo analógico de pH) junto con servidor Web/WebSockets embebido.
  * **Coprocesador de Tiempo Real (Arduino Nano / ATmega328P @ 16 MHz):** Dedicado exclusivamente a detectar el cruce por cero (Zero-Cross ZCS) a 120 Hz de la red de 127 VAC, asegurando el disparo preciso sobre los TRIACs de potencia de las resistencias calefactoras sin interferir con el Wi-Fi o la telemetría del ESP32-S3.
* **Electrónica de Potencia y Control Analógico de Diseño Propio:**
  * **Fuente de Corriente Controlada por Voltaje (VCCS) Pulsada:** Sumidero de corriente lineal balanceado en dos ramas MOSFET (2× MOSFET IRFZ44N con R_shunt = 1 Ω) gobernado por el DAC MCP4725 y lazo cerrado analógico. Permite inyectar corriente continua o trenes de pulsos rectangulares (10 Hz, 20% duty cycle, 1.50 A pico medidos en osciloscopio con sonda de 10 mV/A) para afinar la nucleación del zinc.
* **Soluciones Físico-Químicas de Encapsulado:**
  * Resistencias de inmersión de 450 W encapsuladas en laboratorio usando tubos de vidrio de borosilicato rellenos con óxido de magnesio (MgO) vibro-compactado, protegiéndolas del ataque ácido sin perder conductividad térmica, junto con termopares tipo K aislados con barniz dieléctrico.
* **Desarrollo de Interfaz Web y SCADA Acelerado por Inteligencia Artificial (Industria 4.0):**
  * Un pilar metodológico del proyecto fue aprovechar la **Inteligencia Artificial en su uso más afín y productivo para la ingeniería física**: la programación de software e interfaces. Dado que el equipo concentró su esfuerzo humano en resolver la electrónica de potencia, el control analógico/digital, el encapsulado químico y la experimentación electroquímica, se utilizó asistencia de IA para diseñar y programar la **Interfaz Web responsiva (HTML5/CSS/WebSockets)** embebida en el ESP32-S3, el **sistema SCADA en Python (bajo estándar ISA-88)** con matriz de interlocks de seguridad y la suite de pruebas automatizadas (`pytest`). Esto demuestra cómo la IA permite a equipos de hardware y química construir herramientas de grado industrial en una fracción del tiempo tradicional.

#### 2.3 Aplicaciones Potenciales en Entorno Real
* **Talleres de Galvanoplastia y Acabados:** Modernización (*retrofit*) de tinas empíricas mediante MCUs y módulos accesibles.
* **Laboratorios de I+D y Control de Calidad:** Plataforma automatizada de Celda Hull para validar y optimizar formulaciones químicas de forma repetible y con trazabilidad digital en SCADA.

---

### 3. VENTAJAS COMPETITIVAS E IMPACTO ESPERADO

#### 3.1 Ventajas Técnicas y Comparativa frente a Alternativas

| Parámetro / Característica | Métodos Empíricos (Actual) | Equipos Importados (Atotech/Schlötter) | Nuestra Planta Automatizada (MCUs + SCADA) |
| :--- | :--- | :--- | :--- |
| **Costo de Materiales (BOM)** | Improvisado sin control | Exorbitante ($300,000 - $1,500,000 MXN) | **Ultra bajo costo (< $12,000 MXN)** |
| **Control Térmico** | Manual / On-Off (±8 °C) | PID propietario en PLC cerrado | **Control por Cruce por Cero ZCS (±0.8 °C)** |
| **Generación de Corriente** | Fuente fija no modulada (DC) | Fuentes de pulsos importadas costosas | **VCCS Analógica (DC + Pulsada 10 Hz / 20%)** |
| **Supervisión y Recetas** | Libreta / seguimiento manual | Software propietario con licencia anual | **Interfaz Web Móvil + SCADA ISA-88 asistido por IA** |
| **Seguridad Operativa** | Ninguna (riesgo de sobretemperatura) | Dependiente de PLC de fábrica | **Interlocks de 4 niveles y Watchdog hardware** |
| **Hardware y Refacciones** | Improvisado | Extranjero (semanas de espera) | **MCUs de bajo costo y módulos prefabricados locales** |

#### 3.2 Impacto Medible y Validación Experimental de Métodos Empíricos
Gracias a la automatización de la planta, fue posible ejecutar y validar con precisión electrónica un **Diseño de Experimentos Factorial Multinivel 2⁵ × 4 (128 Corridas)** sobre aluminio 6061-T6 en los laboratorios de CUCEI:
* **Validación Metrológica en Hardware:** Comprobación en osciloscopio (sonda de 10 mV/A) de pulsos limpios de 1.50 A a 10 Hz (20% ciclo útil) y estabilidad térmica de ±0.8 °C.
* **Evaluación de Adherencia bajo Norma ASTM D3359:** Mediante corte enrejado y cinta sobre las zonas de densidad de corriente (`A | B | C | D`) de la Celda Hull, las probetas procesadas con corriente pulsada y control térmico estricto alcanzaron **clasificación 4B/5B (0% de desprendimiento)**, frente a fallas severas (**0B/1B**) del método empírico sin control.
* **Reducción de Mermas y Eficiencia:** Disminución superior al **35% en desperdicio de reactivos** por degradación térmica y validación del software de control mediante **62 pruebas automatizadas (`pytest`, 95% cobertura)**.

#### 3.3 Enfoque de Aplicación en Investigación, Laboratorios de I+D y Transferencia
El sistema no pretende fungir como una línea galvánica de producción fabril masiva, sino que está concebido y dimensionado como una **estación experimental instrumentada y banco de pruebas de bajo costo** para:
1. **Centros de Investigación y Laboratorios Universitarios:** Permitir el estudio sistemático y repetible de fenómenos electroquímicos (cinética de electrodeposición, nucleación por corriente pulsada, comportamiento de aditivos orgánicos y gradientes de Celda Hull de 267 mL) sin requerir equipos extranjeros de cientos de miles de pesos.
2. **Laboratorios de Formulación y Control de Calidad:** Servir a talleres y laboratorios que requieren validar y calibrar recetas antes de introducirlas a líneas grandes, reduciendo mermas de reactivos mediante control de precisión.
3. **Viabilidad de Adopción:** Al basarse en microcontroladores de bajo costo (ESP32-S3 / Arduino Nano) y módulos comerciales estandarizados (adquiribles en distribuidores locales como UNIT Electronics o Emexbit), el costo de la electrónica de control, sensores (pH analógico, MAX6675) y etapas de potencia oscila entre $4,500 y $7,500 MXN. Incluso sumando la Celda Hull acrílica de 267 mL, cubas y resistencias calefactoras, el costo total de la planta piloto no supera los $12,000 a $15,000 MXN, democratizando radicalmente el acceso a experimentación electroquímica rigurosa.

#### 3.4 Equipo Ejecutor
Equipo multidisciplinario de la Universidad de Guadalajara (CUCEI) enfocado en comunicaciones, electrónica, control y química, apalancado en IA para el desarrollo de software e interfaces:
* **Salvador Castro Pérez (Ing. en Comunicaciones y Electrónica):** Arquitectura en MCUs (ESP32-S3 FreeRTOS / ATmega328P), integración de módulos comerciales (I2C/SPI/UART), diseño electrónico e implementación de Interfaz Web y SCADA asistida por IA.
* **Fernando Salvador Samayoa Martínez (Ing. en Comunicaciones y Electrónica):** Diseño analógico de la fuente de corriente VCCS, etapas de potencia con TRIACs, control por cruce por cero y validación en osciloscopio.
* **Víctor Ulises Gutiérrez Ramírez (Ing. Química):** Formulación de electrolitos, encapsulado químico (MgO/borosilicato), diseño de experimentos (2⁵ × 4) en Celda Hull y pruebas de adherencia ASTM D3359.
* **Asesoría Científica:** Respaldados por el Laboratorio de Electroquímica de CUCEI (Dr. Omar González-Meza y Dr. Norberto Casillas), garantizando rigor metodológico en la investigación aplicada.

---
*Expediente integrado para el Premio a la Innovación Mexicana 2026 — Edición Guadalajara.*