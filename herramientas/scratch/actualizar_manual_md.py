# -*- coding: utf-8 -*-
"""
Script para reorganizar la Sección 4 en MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md
Separando limpiamente:
- 4.1 Entorno SCADA de Escritorio en Tiempo Real (Supervisión Viva con Buffer FIFO Limitado)
- 4.2 Suite de Graficación Científica Post-Ensayo a 300 DPI (telemetria/graficar_datos.py)
  con la aclaración de buffer limitado en SCADA vs proceso completo en gráficas,
  disclaimer demostrativo y las guías de cada figura científica.
"""

import re

md_path = r"c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md"

with open(md_path, "r", encoding="utf-8") as f:
    md = f.read()

# Make backup
with open(md_path + ".bak", "w", encoding="utf-8") as f:
    f.write(md)
print("Backup created at .bak")

# Update TOC link
old_toc = "4. [Guía del Operador: Interfaz SCADA y Balanza Gravimétrica](#4-guía-del-operador-interfaz-scada-y-balanza-gravimétrica)"
new_toc = "4. [Guía del Operador: Supervisión SCADA en Tiempo Real y Suite Científica Post-Proceso](#4-guía-del-operador-supervisión-scada-en-tiempo-real-y-suite-científica-post-proceso)"
md = md.replace(old_toc, new_toc)

# Define new Section 4 content
sec4_new = """## 4. Guía del Operador: Supervisión SCADA en Tiempo Real y Suite Científica Post-Proceso

La estación instrumental cuenta con dos entornos de software complementarios diseñados con propósitos analíticos distintos:
1. **Entorno SCADA de Escritorio en Tiempo Real (`telemetria/app.py`):** Supervisión viva a 10 Hz, pilotaje del banco de trabajo y control de fases ISA-88.
2. **Suite de Graficación Científica Post-Proceso (`telemetria/graficar_datos.py` a 300 DPI):** Análisis exhaustivo fuera de línea de la totalidad del experimento (1200+ s) sin límites de buffer.

---

### 4.1 Entorno SCADA de Escritorio en Tiempo Real (Supervisión Viva con Buffer FIFO Limitado)

#### Pasos para Ejecutar un Ensayo en Laboratorio:
1. **Encendido General:**
   * Conectar la fuente de poder principal de $12\\text{V} / 10\\text{A}$ a la red AC.
   * Verificar en el display LED del módulo LM2596 la indicación de **$6.80\\text{ V}$**.
   * Verificar que la baliza LED Neopixel en el ESP32 indique color **Azul** (Standby / Sistema listo).
2. **Iniciar la Aplicación SCADA:**
   * En la computadora de laboratorio, hacer doble clic en el acceso directo **[`Iniciar_Telemetria.bat`](file:///c:/Proyecto/Proyecto/Iniciar_Telemetria.bat)**.
   * La interfaz gráfica Tkinter se abrirá a pantalla completa.
3. **Selección de Receta Experimental (Matriz Taguchi):**
   * En el panel superior, seleccionar el número de placa (1 a 32) de acuerdo con las condiciones planificadas:
     * *Temperatura Celda Hull:* $25^\\circ\\text{C}$ (Ambiente) o $40^\\circ\\text{C}$.
     * *Modo de Corriente:* DC (Corriente Continua) o Pulsado ($10\\text{ Hz}$, ciclo útil $20\\%$).
     * *pH del Baño:* $2.0$ o $4.0$.
4. **Registro de Peso Inicial ($P_{\\text{ini}}$):**
   * Pesar la probeta virgen seca en la balanza analítica del laboratorio (apreciación de $0.1\\text{ mg}$ / $0.0001\\text{ g}$).
   * Presionar el botón **"Iniciar Grabación"** en el software.
   * En la ventana modal de pesaje: escribir el peso inicial (ej. `42.1524`) y presionar *Aceptar*.
5. **Supervisión Automática durante el Ensayo:**
   * El sistema encenderá los calentadores mediante control PI suave, evitando fluctuaciones térmicas.
   * En la Tina 3 (Zincado) y Tina 4 (Niquelado), el sumidero de corriente VCSS activará la rampa suave de corriente (*Soft-Start* de $500\\text{ ms}$) y conmutación a corriente cero (*ZCS*) para proteger la celda.
   * En la pantalla se observará el indicador de **Salud de Celda** (`CELDA_OK` en verde).
6. **Alarma y Pesaje Final ($P_{\\text{fin}}$):**
   * Al concluir la etapa galvánica, sonará una alarma sonora industrial continua.
   * Retirar la placa, enjuagarla con agua desionizada, secarla con flujo suave de aire tibio.
   * Pesar nuevamente en la balanza analítica.
   * Ingresar el peso final en la ventana modal de Faraday (ej. `42.1702`).
7. **Generación de Gráficas y Reporte Científico:**
   * Al presionar **"Exportar Gráficas (300 DPI)"**, el software ejecutará en segundo plano `telemetria/graficar_datos.py`, generando la suite completa de figuras de alta definición en la carpeta del ensayo.

> [!NOTE]
> **Dinámica de Visualización en Tiempo Real (Buffer FIFO Circular):**  
> Los osciloscopios virtuales de la aplicación SCADA en vivo operan mediante una **memoria intermedia circular FIFO (ventana temporal deslizante con buffer de salida acotado)**. Esta arquitectura fue diseñada deliberadamente para mantener una respuesta interactiva fluida a 10 Hz con latencia cero, impidiendo el desbordamiento de memoria RAM o la degradación de la CPU durante jornadas prolongadas de operación. Por tanto, en pantalla viva sólo se visualiza el tramo reciente del ensayo. Para la auditoría, integración analítica y reporte del experimento completo (de 0 a 1200+ segundos), consúltese la **Sección 4.2**.

#### Galería de Pantallas del SCADA en Funcionamiento:

##### 1. Pantalla Principal del SCADA ([`scada_01_principal.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_01_principal.png))
![Pantalla Principal del SCADA](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_01_principal.png)
* **Descripción de la Interfaz:** Centro de comando unificado donde el operador supervisa la telemetría global a 10 Hz.
* **Componentes Principales:**
  * **Columna Izquierda (Gestor de Recetas ISA-88):** Mapeo de la matriz de probetas, selección de ensayo activo (Placa 01 a 1.50 A) y temporizador regresivo de etapa en color cian (`01:24` restantes, 30% completado).
  * **Encabezado Superior:** Tarjetas de proceso de las 4 tinas con ángulo de disparo (&alpha;) y potencia disipada (T1 83.0°C / SP 85°C, 101.2W; T2 82.9°C / SP 85°C, 90.0W; T3 25.0°C / SP 25°C, 1.4W; T4 34.1°C / SP 35°C, 65.2W), carga acumulada ($Q = 232.6\\text{ C}$), corriente galvánica ($1.50\\text{ A}$), pH de sondas ($4.00 / 5.73$) y botones de acceso rápido a ventanas modulares.
  * **Panel Central (Osciloscopios en Streaming):** 3 gráficos en tiempo real: (1) Temperatura multizona en °C, (2) Porcentaje de modulación de compuerta TRIAC (%) y (3) Corriente galvánica inyectada por el sumidero VCSS (1.50 A).

---

##### 2. Ventana Modular: Osciloscopio Digital de Actuadores y Conmutación AC ([`scada_02_actuadores.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_02_actuadores.png))
![Ventana de Osciloscopio y Actuadores](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_02_actuadores.png)
* **Descripción de la Interfaz:** Módulo de inspección eléctrica profunda para auditar la física de conmutación de los optoacopladores MOC3021 y los TRIACs BTA24-600B.
* **Componentes Principales:**
  * **Selectores Superiores:** Alternancia entre *Recorte de Fase (&alpha;)* y *Burst Fire / Proporcional (ZCS)*, con pestañas independientes para las 4 tinas (T1 a T4), el sumidero VCSS y la vista consolidada 2×2.
  * **Panel de 3 Canales Sincronizados:**
    1. *Tensión de Carga AC:* Forma de onda recortada de 60 Hz comparada contra la red de 120 VAC.
    2. *Pulsos de Disparo de Compuerta (Gate):* Tren de pulsos TTL de 5V inyectados al pin de disparo del MOC3021 con el retardo exacto de fase ($5711\\,\\mu\\text{s}$).
    3. *Potencia Activa Instantánea:* Curva disipada $p(t) = v(t)^2 / R$ y potencia media cuadrática ($101.2\\text{ W}$).
  * **Barra Inferior de KPIs Eléctricos:** Esfuerzo $u(t) = 22.5\\%$, ángulo $\\alpha = 123.4^\\circ$, retardo de compuerta $5711\\,\\mu\\text{s}$, tensión cuadrática media $V_{\\text{RMS}} = 49.2\\text{ V}$, potencia activa disipada $101.2\\text{ W}$ y corriente del sumidero $1.50\\text{ A}$.

---

##### 3. Ventana Modular: Dinámica de Errores e Índices IAE / Retrato de Fase ([`scada_03_errores.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_03_errores.png))
![Ventana de Errores y Plano de Fase](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_03_errores.png)
* **Descripción de la Interfaz:** Entorno de teoría de control en tiempo real para supervisar la estabilidad analítica de los 4 lazos cerrados PI.
* **Componentes Principales:**
  * **Gráfica Superior (Desviación Térmica Temporal):** Curvas de error $e(t) = SP - PV$ en °C para cada tina convergiendo suavemente hacia la banda de alta precisión de $\\pm 0.5^\\circ\\text{C}$.
  * **Gráfica Intermedia (Retrato de Fase en Espacio de Estados):** Diagrama $de/dt$ vs. $e(t)$ donde las trayectorias espirales colapsan hacia el atractor de estabilidad en el origen $(0, 0)$.
  * **Gráfica Inferior (Desviación Galvánica VCSS):** Error de corriente galvánica en Amperes respecto a la consigna nominal.
  * **Métricas IAE y Diagnóstico de Estado:** Contadores numéricos de IAE acumulado (T1: 1660.8, T2: 1766.9, T3: 9.4, T4: 422.7 °C·s), derivada térmica instantánea ($+0.020^\\circ\\text{C/s}$), error de corriente ($+0.00\\text{ A}$) y confirmación de estabilidad: `🟢 EN ATRACTOR (±0.5°C | Estacionario)`.

---

##### 4. Ventana Modular: Balanza Gravimétrica y Rendimiento Faradaico ([`scada_04_faraday.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_04_faraday.png))
![Ventana de Balanza y Ley de Faraday](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_04_faraday.png)
* **Descripción de la Interfaz:** Módulo analítico para procesar las pesadas de laboratorio y verificar la cinética electroquímica según las Leyes de Faraday.
* **Componentes Principales:**
  * **Formulario de Entradas de Laboratorio:** Selector de metal (Zinc $\\text{Zn}^{2+}$, Níquel $\\text{Ni}^{2+}$ o Auto), campos numéricos para peso inicial en balanza analítica ($42.1524\\text{ g}$), peso final con recubrimiento seco ($42.1702\\text{ g}$) y área sumergida de la probeta ($65.0\\text{ cm}^2$).
  * **Resultados Culombimétricos Calculados:** Carga eléctrica integrada ($Q = 232.6\\text{ C}$ / $64.6\\text{ mAh}$), masa teórica de Faraday ($m_{\\text{teo}} = 78.79\\text{ mg}$), masa real experimental depositada ($\\Delta m = 17.80\\text{ mg}$), eficiencia Faradaica ($\\eta_F = 22.6\\%$) y espesor medio estimado ($0.38\\,\\mu\\text{m}$).
  * **Lienzos Gráficos Integrados:** (1) Acumulación cronológica de carga eléctrica $Q(t) = \\int I(t)dt$ en Coulombs y (2) Curva de masa teórica creciente vs. línea horizontal de masa experimental medida gravimétricamente.

---

##### 5. Ventana Modular: Metrología y Calibración Nernstiana de pH Dual ([`scada_05_ph.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_05_ph.png))
![Ventana de Metrología y Calibración de pH](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_05_ph.png)
* **Descripción de la Interfaz:** Módulo metrológico para calibrar las sondas de electrodo de vidrio combinadas sobre el convertidor ADS1115 de 16 bits.
* **Componentes Principales:**
  * **Gráfico 1 (Dinámica de Estabilización y Oscilaciones):** Traza el potencial analógico bruto en Voltios y el pH calculado en tiempo real para verificar el criterio de estabilidad $|dV/dt| < 10\\text{ mV}$ durante 3 segundos antes de registrar el punto.
  * **Gráfico 2 (Curva Nernstiana Experimental vs. Teórica):** Recta de regresión sobre los tampones patrón de pH 4.01, 7.00 y 10.01 comparada contra la pendiente ideal de Nernst ($59.16\\text{ mV/pH}$ a $25^\\circ\\text{C}$), certificando $R^2 = 1.000$.
  * **Panel de Control y Diagnóstico de Sonda:** Indicador digital de alta visibilidad (`6.99 pH`, $1.767\\text{ V}$), cálculo de sensibilidad experimental ($235.67\\text{ mV/pH}$), diagnóstico de salud de la sonda (`Slope: 110.0% ÓPTIMA`), botones de captura de buffers, botón de guardado en la memoria Flash NVS del ESP32 y exportación de certificados metrológicos a 300 DPI.

---

##### 6. Ventana Modular: Diagnóstico de Hardware, Buses y Auditoría de Incidentes ([`scada_06_diagnostico.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_06_diagnostico.png))
![Ventana de Diagnóstico de Hardware y Sensores](file:///c:/Proyecto/Proyecto/documentos/imagenes/scada_06_diagnostico.png)
* **Descripción de la Interfaz:** Tablero de supervisión de bajo nivel del hardware embebido, estado de los buses I2C/SPI y registro en tiempo real de anomalías operativas.
* **Componentes Principales:**
  * **Tarjetas de Estado de Periféricos I2C (GPIO 8/9 — 400 kHz):** Monitoreo de AHT20 (`0x38`), BMP280 (`0x76/77`), ADS1115 (`0x48`) y MCP4725 (`0x60`), todos con estado `🟢 OK (Conectado)`.
  * **Tarjetas de Termopares SPI MAX6675 (CS 5, 4, 13, 14):** Monitoreo de continuidad eléctrica de los termopares de T1 a T4, con estado `🟢 OK (0-150°C)`.
  * **Tabla de Auditoría de Incidentes en Tiempo Real:** Lista cronológica con severidad codificada por colores (`INFO`, `ADVERTENCIA`, `CRÍTICO`) donde se auditan eventos como sincronización de ADC a 860 SPS, alcance de estabilidad isotérmica, balance térmico en shunts de corriente y carga acumulada.
  * **Barra de Pruebas de Auditoría:** Botones para simular perturbaciones controladas (salto térmico de +16°C, desconexión de sonda T1, sobretemperatura en T4, desbalance de shunts VCSS) para validar el comportamiento del logger y las alarmas de seguridad antes de los ensayos químicos.

---

### 4.2 Suite de Graficación Científica Post-Ensayo a 300 DPI (`telemetria/graficar_datos.py`)

> [!IMPORTANT]
> **CLARIFICACIÓN ARQUITECTÓNICA: SUPERVISIÓN SCADA EN VIVO vs. SUITE DE GRAFICACIÓN CIENTÍFICA**  
> * **1. Entorno SCADA de Escritorio en Tiempo Real (Sección 4.1):** Sistema interactivo optimizado para supervisión viva y control a **10 Hz**. Debido a que un ensayo continuo puede prolongarse durante horas, mantener en memoria viva millones de muestras generaría fugas de memoria RAM y congelaría la interfaz gráfica. Por ello, opera con una **memoria intermedia circular FIFO (buffer deslizante limitado)** que refresca únicamente la ventana temporal más reciente.  
> * **2. Suite Científica Post-Proceso a 300 DPI (Esta Sección 4.2):** Se ejecuta una vez concluido el ensayo leyendo directamente el archivo CSV íntegro almacenado en el disco duro. **No posee limitación de buffer**, por lo que procesa de principio a fin **la totalidad del experimento (todos los 1200+ segundos / 20+ minutos de datos)**. Esto permite calcular integrales analíticas continuas (energía en Wh, carga culombimétrica total $Q$, índice IAE acumulado), modelar envolventes de los 72,000 ciclos senoidales a 60 Hz y compilar figuras compuestas de resolución editorial a 300 DPI.  
> * *En resumen: el SCADA le permite operar y controlar la planta en el presente; la Suite de Graficación le permite auditar, certificar y documentar el pasado histórico completo del proceso.*

> [!WARNING]
> **Descargo de Responsabilidad Metrológica (Gráficas Demostrativas):**  
> Todas las curvas, oscilogramas y gráficas científicas expuestas en esta sección son de carácter **estrictamente demostrativo y educativo**. Fueron generadas mediante modelos numéricos y datos simulados para exhibir la capacidad analítica de la plataforma y no corresponden a ningún proceso químico real ni lote industrial de producción.

#### 4.2.1 Compilador Automatizado y Flujo de Trabajo
Al concluir un ensayo, el investigador ejecuta el motor científico mediante:
```bash
python telemetria/graficar_datos.py --experimento "telemetria/experimentos/Ensayo_2026-09-12_14-30-00" --dpi 300
```
El compilador lee el CSV sin pérdida de resolución temporal, calcula derivadas térmicas, integra energía activa y genera los archivos vectoriales y rasterizados de alta densidad que se detallan a continuación.

---

#### 4.2.2 Perfil Electroquímico y Térmico Multizona ([`01_perfil_electroquimico_termico.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/01_perfil_electroquimico_termico.png))
![Perfil Electroquímico y Térmico Multizona](file:///c:/Proyecto/Proyecto/documentos/imagenes/01_perfil_electroquimico_termico.png)
* **📌 ¿Por qué se añade esta gráfica?:** Es el documento central de validación fisicoquímica del proceso completo. Permite verificar que cada tina alcanzó su temperatura de consigna antes de autorizar la inmersión de la probeta, y que la corriente galvánica se mantuvo estable sin caídas durante toda la fase de electrodeposición.
* **📊 ¿Qué representa?:** Dos paneles sincronizados a lo largo de 1200 segundos (20 minutos): el panel superior traza las curvas de temperatura de las 4 tinas ($^\\circ\\text{C}$) contrastadas contra sus consignas punteadas; el panel inferior muestra la corriente galvánica real ($A$) frente a la consigna del sumidero VCSS.
* **📖 ¿Cómo se lee e interpreta?:**
  * *Calentamiento Inicial:* Rampas de subida suaves con pendientes de $1.5\\text{ a }2.0^\\circ\\text{C/min}$ y sobretiro prácticamente nulo (*overshoot* $< 0.8^\\circ\\text{C}$).
  * *Meseta Isotérmica:* Las 4 temperaturas se aplanan dentro de la franja de tolerancia ($\\pm 0.5^\\circ\\text{C}$).
  * *Escalón de Corriente:* Arranque suave (*Soft-Start* de $500\\text{ ms}$) y meseta perfectamente horizontal durante los 10 minutos de electrólisis.
  * *Diagnóstico de Anomalías:* Caídas térmicas bruscas indican adición imprevista de agua fría o retiro de tapas; fluctuaciones en la corriente indican pasivación del ánodo o falsos contactos.

---

#### 4.2.3 Seguimiento de Errores de Control e Índice Acumulativo IAE ([`02_seguimiento_errores_control.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/02_seguimiento_errores_control.png))
![Seguimiento de Errores e Índices IAE](file:///c:/Proyecto/Proyecto/documentos/imagenes/02_seguimiento_errores_control.png)
* **📌 ¿Por qué se añade esta gráfica?:** Proporciona la métrica matemática más estricta de la ingeniería de control para calificar el desempeño del lazo cerrado. Mientras que una curva de temperatura puede disimular desviaciones leves, el índice integral IAE ($\\int_0^t |e(\\tau)|\\,d\\tau$) acumula cualquier desvío en el tiempo, permitiendo certificar la sintonía PI sin sesgos visuales.
* **📊 ¿Qué representa?:** Dos paneles apilados: el superior grafica el error instantáneo $e(t) = SP - T(t)$ en $^\\circ\\text{C}$ con su banda de tolerancia ($\\pm 0.5^\\circ\\text{C}$); el inferior muestra la curva monótona creciente de acumulación de error IAE en [$^\\circ\\text{C} \\cdot \\text{s}$] para cada tina.
* **📖 ¿Cómo se lee e interpreta?:**
  * *Error Instantáneo:* Al arrancar desciende desde un error alto (ej. $+60^\\circ\\text{C}$) y converge a la franja de $\\pm 0.5^\\circ\\text{C}$ centrada en cero.
  * *Índice IAE:* Sube durante la fase de calentamiento, pero una vez alcanzada la consigna **debe aplanarse totalmente y convertirse en una línea horizontal**.
  * *Diagnóstico de Anomalías:* Si la curva IAE continúa ascendiendo con pendiente constante durante el régimen permanente, delata un error de estado estacionario no corregido por falta de ganancia integral $K_i$.

---

#### 4.2.4 Esfuerzo de Control de TRIACs y Potencia RMS ([`03_actuadores_triacs_potencia.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/03_actuadores_triacs_potencia.png))
![Esfuerzo de Control de TRIACs y Potencia RMS](file:///c:/Proyecto/Proyecto/documentos/imagenes/03_actuadores_triacs_potencia.png)
* **📌 ¿Por qué se añade esta gráfica?:** Para auditar el estrés eléctrico y térmico soportado por los semiconductores de potencia (TRIACs BTA24-600B) y verificar la potencia real consumida en Watts por las resistencias calefactoras sin requerir instrumental externo.
* **📊 ¿Qué representa?:** Tres paneles sincronizados: ángulo de retardo de disparo $\\alpha(t)$ en grados ($0^\\circ\\text{ a }180^\\circ$), tensión eficaz cuadrática $V_{\\text{RMS}}(t)$ aplicada sobre la resistencia y potencia activa disipada $P(t) = V_{\\text{RMS}}^2 / R$ en Watts para cada tina.
* **📖 ¿Cómo se lee e interpreta?:**
  * *Arranque:* $\\alpha$ se sitúa en $0^\\circ\\text{--}25^\\circ$, produciendo $V_{\\text{RMS}} \\approx 115\\text{--}120\\text{ V}$ y $P \\approx 450\\text{ W}$ (plena potencia nominal).
  * *Régimen Permanente:* $\\alpha$ se abre progresivamente a $120^\\circ\\text{--}140^\\circ$, la tensión eficaz cae a $45\\text{--}55\\text{ V}$ y la potencia se reduce a $70\\text{--}90\\text{ W}$ (compensación exacta de pérdidas térmicas).
  * *Diagnóstico de Anomalías:* Si la potencia permanece fija al 100% y la temperatura no sube, la resistencia calefactora está abierta o desconectada.

---

#### 4.2.5 Macro-Conmutación de TRIACs a lo largo de Todo el Proceso ([`03b_macro_conmutacion_4tinas_proceso_completo.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/03b_macro_conmutacion_4tinas_proceso_completo.png))
![Macro-Conmutación de TRIACs en las 4 Tinas](file:///c:/Proyecto/Proyecto/documentos/imagenes/03b_macro_conmutacion_4tinas_proceso_completo.png)
* **📌 ¿Por qué se añade esta gráfica?:** En sistemas de control convencionales, solo se grafica la curva de temperatura ($T$ vs. $t$). Dicha curva únicamente muestra la variable de salida (PV), pero **oculta por completo la dinámica interna del actuador**: no revela si los TRIACs operaron saturados, si sufrieron conmutaciones parásitas violentas (*chattering*), o si el algoritmo PI introdujo oscilaciones encubiertas de potencia. Esta figura brinda una **auditoría ciberfísica global y continua en las 4 tinas simultáneas a lo largo de los 1200 segundos del proceso**.
* **📊 ¿Qué representa?:** Una matriz comparativa de 4 Filas (las 4 cubas) &times; 2 Columnas:
  * *Columna Izquierda (Recorte de Ángulo de Fase $\\alpha$):* Muestra la envolvente instantánea conducida ($\\pm V_{\\text{peak}} = \\pm 170\\text{ V}$), la tensión cuadrática media $V_{\\text{RMS}}(t)$ y el ángulo de disparo $\\alpha(t)$ en grados.
  * *Columna Derecha (Tiempo Proporcional / Burst Firing ZCS):* Muestra los estados lógicos de conducción activa ($100\\%$) y reposo ($0\\%$) junto con la potencia disipada en Watts.
  * *Eje Gemelo Derecho:* Temperatura real medida en el seno del líquido por el termopar tipo K en $^\\circ\\text{C}$ (trazo continuo) comparada contra la consigna programada (línea punteada *setpoint*).
* **🔬 Física de la Portadora Senoidal de 60 Hz y Origen Óptico del «Bloque Rectangular Sólido»:**  
  En la red eléctrica de 60 Hz, cada ciclo senoidal completo dura exactamente $16.66\\text{ ms}$. A lo largo de un ensayo de 20 minutos ($1200\\text{ s}$), ocurren exactamente **72,000 ciclos senoidales completos (144,000 excursiones entre +170V y -170V pico)**.
  En una pantalla estándar de 1920 píxeles de ancho, **un solo píxel horizontal abarca más de 37 ciclos senoidales completos**. Al trazar la tensión oscilando 60 veces por segundo, las líneas quedan tan densamente compactadas que se solapan físicamente: el ojo humano y la resolución gráfica perciben un **bloque rectangular sólido y homogéneo de color** entre $+170\\text{ V}$ y $-170\\text{ V}$.
  Para modelar este fenómeno con máxima fidelidad sin congelar el procesador con 14.4 millones de puntos, el generador científico traza la **envolvente matemática de cresta ($\\pm V_{\\text{peak}}$) con relleno sombreado (`fill_between`) y la curva eficaz $V_{\\text{RMS}}(t)$**.
* **📖 ¿Cómo se lee e interpreta la transición de 3 firmas geométricas?:**
  1. *El «Rectángulo Sólido» (Calentamiento al 95–100%):* Bloque denso en los primeros $300\\text{--}500\\text{ s}$; el opto-TRIAC conduce ininterrumpidamente para romper la inercia térmica ($450\\text{ W}$).
  2. *La «Zona Estriada / Código de Barras» (Transición y Frenado PI al 50%):* Franjas verticales alternadas con espacios en cero voltios al entrar la temperatura a la banda proporcional ($|T - SP| \\le 5^\\circ\\text{C}$).
  3. *Los «Pulsos Delgados Periódicos Espaciados» (Régimen Permanente al 15–20%):* El rectángulo desaparece; solo se aprecian pulsos delgados uniformes ($70\\text{--}90\\text{ W}$), certificando formalmente el **asentamiento térmico ($\\pm 0.5^\\circ\\text{C}$)**.

---

#### 4.2.6 Senoidales Modificadas por TRIAC en Escala Microscópica ([`03_senoidales_modificadas_periodos.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/03_senoidales_modificadas_periodos.png))
![Senoidales modificadas en escala microscópica](file:///c:/Proyecto/Proyecto/documentos/imagenes/03_senoidales_modificadas_periodos.png)
* **📌 ¿Por qué se añade esta gráfica?:** Proporciona la resolución temporal de un osciloscopio de laboratorio (0 a 50 ms) para inspeccionar la morfología íntima de la onda senoidal y contrastar el mecanismo físico del recorte de fase frente a los paquetes de ciclos enteros (Burst Firing).
* **📊 ¿Qué representa?:** La tensión instantánea $v(t)$ en tres condiciones operativas: Esfuerzo Máximo (Calentamiento al 95%), Transición (Banda Proporcional al 50%) y Régimen Permanente (Asentamiento al 15%).
* **📖 ¿Cómo se lee e interpreta?:**
  * *Fila Recorte de Fase:* La onda permanece en 0V al cruzar por cero y salta abruptamente a la senoidal al alcanzarse el ángulo $\\alpha$. A mayor ángulo, menor área conducida y menor calor disipado.
  * *Fila Burst Firing:* Conduce ondas senoidales completas sin cortes intermedios, suprimiendo la emisión electromagnética (EMI).

---

#### 4.2.7 Análisis Faradaico y Cinética de Electrodeposición ([`04_analisis_faraday_plano_fase.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/04_analisis_faraday_plano_fase.png))
![Análisis Faradaico y Cinética Electroquímica](file:///c:/Proyecto/Proyecto/documentos/imagenes/04_analisis_faraday_plano_fase.png)
* **📌 ¿Por qué se añade esta gráfica?:** Es el entregable químico primordial para certificar la calidad del depósito galvánico. Correlaciona la carga eléctrica consumida ($Q = \\int I dt$), la masa teórica predicha por Faraday y la masa gravimétrica real pesada en balanza analítica, calculando la eficiencia de corriente ($\\eta\\%$) y el espesor del depósito ($\\mu\\text{m}$).
* **📊 ¿Qué representa?:** Curva de acumulación de carga eléctrica en Coulombs ($Q$ vs $t$), masa teórica vs. masa real en gramos ($\\Delta m$) e indicador porcentual de eficiencia Faradaica ($\\eta_F\\%$).
* **📖 ¿Cómo se lee e interpreta?:**
  * *Carga Eléctrica:* Línea recta con pendiente uniforme durante el paso de corriente ($dQ/dt = I$).
  * *Eficiencia de Corriente:* Valores esperados entre $90\\%\\text{ y }98\\%$ para zincado ácido, y $85\\%\\text{ a }95\\%$ para niquelado de Watts.
  * *Diagnóstico de Anomalías:* Rendimientos $\\eta < 80\\%$ indican sobrepotencial catódico excesivo con evolución violenta de hidrógeno gas ($\\text{H}_2 \\uparrow$) y riesgo de fragilización por hidrógeno.

---

#### 4.2.8 Dashboard Ejecutivo Post-Ensayo y Balance de Energía en Wh ([`05_diagnostico_integral_resumen.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/05_diagnostico_integral_resumen.png))
![Dashboard Ejecutivo de Diagnóstico](file:///c:/Proyecto/Proyecto/documentos/imagenes/05_diagnostico_integral_resumen.png)
* **📌 ¿Por qué se añade esta gráfica?:** Condensa en un resumen gerencial único el balance técnico, el costo energético en KWh y los indicadores de desempeño (KPIs) para fines de auditoría técnica y control de calidad sin tener que inspeccionar archivos CSV crudos.
* **📊 ¿Qué representa?:** Gráfico de barras de consumo energético acumulado por tina en Watt-hora ($\\text{Wh}$), radar de desempeño de control (IAE, tiempo de establecimiento, estabilidad galvánica) y tabla resumen de eventos.
* **📖 ¿Cómo se lee e interpreta?:**
  * *Distribución de Energía:* Tinas 1 y 2 ($85^\\circ\\text{C}$) concentran el 80–90% de la energía total; Tina 3 (Celda Hull) registra un consumo mínimo ($< 15\\text{ Wh}$).
  * *Radar de Control:* Cuanto mayor sea la superficie del polígono verde, mayor fue la excelencia del lazo.

---

#### 4.2.9 Cronograma Gantt de Etapas ISA-88 y Tiempos Muertos ([`06_tiempos_muertos_gantt_fases.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/06_tiempos_muertos_gantt_fases.png))
![Cronograma Gantt de Etapas ISA-88](file:///c:/Proyecto/Proyecto/documentos/imagenes/06_tiempos_muertos_gantt_fases.png)
* **📌 ¿Por qué se añade esta gráfica?:** Audita la repetibilidad temporal de cada fase de tratamiento químico y los tiempos de transferencia aérea entre tinas, asegurando que no existan retrasos que provoquen pasivación superficial por exposición al oxígeno ambiental.
* **📊 ¿Qué representa?:** Diagrama cronológico de Gantt que mapea las etapas del proceso (Desengrase, Enjuagues, Decapado, Zincado, Niquelado) contra el tiempo en segundos y minutos, identificando tiempos activos de inmersión y tiempos de transferencia.
* **📖 ¿Cómo se lee e interpreta?:**
  * *Barras de Etapa:* Longitud idéntica a la programada en la matriz de recetas.
  * *Tiempos de Transferencia:* Las barras de transición deben ser inferiores a 15 segundos para evitar pasivación aérea de la probeta.

---

#### 4.2.10 Metrología VCSS y Muestreo Estroboscópico ETS a 10 Hz ([`08_metrologia_vcss_ets_pulsado.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/08_metrologia_vcss_ets_pulsado.png))
![Metrología VCSS y Muestreo ETS](file:///c:/Proyecto/Proyecto/documentos/imagenes/08_metrologia_vcss_ets_pulsado.png)
* **📌 ¿Por qué se añade esta gráfica?:** Audita la fidelidad del escalón de corriente del sumidero analógico regulado por el MCP4725 y el LM358, verificando que no existan sobreoscilaciones ni distorsiones por inductancia parásita de la cuba.
* **📊 ¿Qué representa?:** Reconstrucción a escala de milisegundos mediante la técnica ETS (*Equivalent Time Sampling*), contrastando la consigna analógica del DAC MCP4725 contra la corriente real sensada por el conversor ADS1115 de 16 bits sobre los shunts cerámicos de 10W.
* **📖 ¿Cómo se lee e interpreta?:**
  * *Tiempos de Flanco:* Subida ($t_r < 1.0\\text{ ms}$) y bajada ($t_f < 1.0\\text{ ms}$) con transiciones nítidas.
  * *Meseta del Pulso:* Horizontal y plana con error cuadrático inferior al $1.5\\%$.

---

#### 4.2.11 Metrología de pH y Filtrado Digital Tri-Modo ([`08_filtro_ph_tri_modo.png`](file:///c:/Proyecto/Proyecto/documentos/imagenes/08_filtro_ph_tri_modo.png))
![Metrología de pH y Filtrado Digital](file:///c:/Proyecto/Proyecto/documentos/imagenes/08_filtro_ph_tri_modo.png)
* **📌 ¿Por qué se añade esta gráfica?:** Garantiza la trazabilidad metrológica de la acidez en la Celda Hull de zincado ácido (pH nominal 2.0 a 4.0) y demuestra la efectividad del filtro digital eliminando spikes de conmutación sin retardar la respuesta.
* **📊 ¿Qué representa?:** El panel izquierdo muestra la recta de regresión de Nernst validando que la pendiente experimental sea $\\ge 95\\%$ del valor teórico ($59.16\\text{ mV/pH}$ a $25^\\circ\\text{C}$); el panel derecho compara la señal ruidosa del electrodo de vidrio frente a la curva limpia del filtro de mediana y ventana móvil.
* **📖 ¿Cómo se lee e interpreta?:**
  * La pendiente experimental debe aproximarse a $59.16\\text{ mV/pH}$ con $R^2 \\ge 0.995$.
  * La curva filtrada debe mantenerse suave y estable aún durante los disparos de corriente del sumidero VCSS.

---

"""

# Regex to match Section 4 in MD
patt_sec4 = re.compile(r'## 4\. Guía del Operador: Interfaz SCADA y Balanza Gravimétrica.*?---.*?---.*?(?=## 5\. Modelado y Cálculos de Eficiencia Faradaica y Espesor)', re.DOTALL)

if patt_sec4.search(md):
    md = patt_sec4.sub(lambda m: sec4_new, md)
    print("Section 4 replaced successfully using regex!")
else:
    print("Regex didn't match directly, checking with broader boundary...")
    patt_sec4_broad = re.compile(r'## 4\. Guía del Operador.*?(?=## 5\. Modelado y Cálculos de Eficiencia Faradaica y Espesor)', re.DOTALL)
    if patt_sec4_broad.search(md):
        md = patt_sec4_broad.sub(lambda m: sec4_new, md)
        print("Section 4 replaced successfully using broad pattern!")
    else:
        print("ERROR: Section 4 pattern not found in MD!")

with open(md_path, "w", encoding="utf-8") as f:
    f.write(md)

print("MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md updated successfully!")
