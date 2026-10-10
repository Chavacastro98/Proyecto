/**
 * Showcase Técnico CTS-C51 | SMEQ 2026
 * MÓDULO PRINCIPAL: Navegación por pestañas, Lightbox de inspección y Ciclo de vida
 */

// GESTOR DE PESTAÑAS (TABS)
const tabs = document.querySelectorAll('.tab-btn');
const panels = document.querySelectorAll('.tab-panel');

tabs.forEach(btn => {
  btn.addEventListener('click', () => {
    const targetId = btn.getAttribute('data-tab');
    if (!targetId) return;

    tabs.forEach(t => t.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));

    btn.classList.add('active');
    const targetPanel = document.getElementById(targetId);
    if (targetPanel) {
      targetPanel.classList.add('active');
      if (typeof actualizarSimuladorTermico === 'function' && targetId === 'tab-termico') actualizarSimuladorTermico();
      if (typeof actualizarOndaCuadrada === 'function' && targetId === 'tab-vcss') actualizarOndaCuadrada();
      if (typeof actualizarCalculadoraPh === 'function' && targetId === 'tab-ph') actualizarCalculadoraPh();
    }
  });
});

// =========================================================================
// MODAL DE IMÁGENES / LIGHTBOX HD CON ZOOM Y PAN INTERACTIVO
// =========================================================================
let modalZoom = 1.0;
let modalPanX = 0;
let modalPanY = 0;
let isDraggingModal = false;
let startDragX = 0;
let startDragY = 0;

function actualizarTransformModal() {
  const modalImg = document.getElementById('modalImg');
  if (!modalImg) return;
  modalImg.style.transform = `translate(${modalPanX}px, ${modalPanY}px) scale(${modalZoom})`;
  const badge = document.getElementById('modalZoomBadge');
  if (badge) badge.textContent = `${Math.round(modalZoom * 100)}%`;
}

function cambiarZoomModal(delta) {
  modalZoom = Math.min(5.0, Math.max(0.4, Math.round((modalZoom + delta) * 100) / 100));
  if (modalZoom === 1.0) {
    modalPanX = 0;
    modalPanY = 0;
  }
  actualizarTransformModal();
}

function resetZoomModal() {
  modalZoom = 1.0;
  modalPanX = 0;
  modalPanY = 0;
  actualizarTransformModal();
}

function abrirModal(src, titulo) {
  const modal = document.getElementById('modalOverlay');
  const modalImg = document.getElementById('modalImg');
  const modalTitle = document.getElementById('modalTitle');
  const modalExt = document.getElementById('modalExternalLink');
  if (!modal || !modalImg) return;

  modalImg.src = src;
  if (modalTitle) modalTitle.textContent = titulo || 'Inspección Técnica en Alta Resolución';
  if (modalExt) modalExt.href = src;

  resetZoomModal();
  modal.classList.add('open');
}

function cerrarModal(e) {
  if (e && e.target && e.target !== e.currentTarget && !e.target.classList.contains('modal-close')) return;
  const modal = document.getElementById('modalOverlay');
  if (modal) modal.classList.remove('open');
  resetZoomModal();
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const modal = document.getElementById('modalOverlay');
    if (modal) modal.classList.remove('open');
    resetZoomModal();
  }
});

// GESTIÓN DEL DIAGRAMA MAESTRO [00]: FLUJO LÓGICO Y CONCURRENCIA RTOS 2.0 (MERMAID VECTORIAL)
let vistaMaestroActual = 'mermaid';

function cambiarVistaMaestro(vista) {
  vistaMaestroActual = 'mermaid';
  const vMermaid = document.getElementById('vistaMaestroMermaid');
  if (vMermaid) vMermaid.style.display = 'block';
  const btnExt = document.getElementById('btnAbrirMaestroExt');
  if (btnExt) btnExt.href = 'assets/diagramas/00_arquitectura_distribuida.svg';
}

function inspeccionarMaestroActual() {
  abrirModal(
    'assets/diagramas/00_arquitectura_distribuida.svg',
    'Diagrama Maestro 00: Arquitectura Distribuida y Concurrencia RTOS 2.0 (ESP32-S3 Dual-Core SMP, Core 0 Web y Core 1 Control)'
  );
}

// INICIALIZACIÓN GLOBAL
window.addEventListener('DOMContentLoaded', () => {
  if (typeof actualizarSimuladorTermico === 'function') actualizarSimuladorTermico();
  if (typeof actualizarOndaCuadrada === 'function') actualizarOndaCuadrada();
  if (typeof actualizarCalculadoraPh === 'function') actualizarCalculadoraPh();
  if (typeof actualizarCalculadoraFaraday === 'function') actualizarCalculadoraFaraday();
  if (typeof seleccionarNodoArch === 'function') seleccionarNodoArch('esp32');

  // Configuración de gestos y zoom interactivo en Modal HD
  const modalBody = document.getElementById('modalBody');
  const modalImg = document.getElementById('modalImg');

  if (modalBody && modalImg) {
    // Zoom con rueda del ratón
    modalBody.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.25 : -0.25;
      cambiarZoomModal(delta);
    }, { passive: false });

    // Arrastre con ratón
    modalBody.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      isDraggingModal = true;
      startDragX = e.clientX - modalPanX;
      startDragY = e.clientY - modalPanY;
      modalImg.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDraggingModal) return;
      modalPanX = e.clientX - startDragX;
      modalPanY = e.clientY - startDragY;
      actualizarTransformModal();
    });

    window.addEventListener('mouseup', () => {
      if (isDraggingModal) {
        isDraggingModal = false;
        if (modalImg) modalImg.style.cursor = 'grab';
      }
    });

    // Doble clic para alternar entre 100% y 200%
    modalImg.addEventListener('dblclick', (e) => {
      e.preventDefault();
      if (modalZoom > 1.05) {
        resetZoomModal();
      } else {
        modalZoom = 2.0;
        actualizarTransformModal();
      }
    });
  }
});

window.addEventListener('resize', () => {
  if (typeof actualizarSimuladorTermico === 'function') actualizarSimuladorTermico();
  if (typeof actualizarOndaCuadrada === 'function') actualizarOndaCuadrada();
  if (typeof actualizarCalculadoraPh === 'function') actualizarCalculadoraPh();
});

// CONTROLADOR DEL DIAGRAMA DE ARQUITECTURA VECTORIAL INTERACTIVO
const ARCH_NODOS = {
  esp32: {
    titulo: 'Master: ESP32-S3 N16R8 Dual-Core @ 240 MHz (RTOS 2.0)',
    chip: 'Espressif Systems ESP32-S3-WROOM-1',
    pines: 'Dual Core LX7, 512KB SRAM, 8MB PSRAM Octal, 16MB Flash SPI',
    bus: 'Coordinador Maestro: I²C Fast-Mode (GPIO 8/9), SPI @ 4MHz (GPIO 18/19/5/4/13/14), UART2 (GPIO 17 TX)',
    desc: 'Núcleo central del sistema gobernado por FreeRTOS SMP Dual-Core. Core 0 ejecuta la pila de comunicaciones Wi-Fi SoftAP ("Uli"), servidor Web HTTP en puerto 80 con endpoint unificado /data_all a 10 Hz y servicio de actualización remota OTA. Core 1 ejecuta en tiempo real determinístico los 4 lazos de control PI térmicos (1 Hz), modulación analógica de corriente VCSS (Gm = 2.00 S), adquisición continua del sensor de pH en Canal A1 dedicado a 860 SPS y máquina de seguridad Fail-Safe (50 Hz).'
  },
  nano: {
    titulo: 'Esclavo de Potencia: Arduino Nano Coprocesador Nano2 @ 16 MHz',
    chip: 'ATmega328P / Microchip',
    pines: 'D3 (INT1 Cruce por Cero), D7-D10 (Compuertas TRIACs T0-T3), D0 (RX UART @ 9600 bps)',
    bus: 'UART2 Esclavo @ 9600 Baud + Interrupción externa INT1 (Pin D3 ZCD)',
    desc: 'Coprocesador dedicado a la modulación de potencia térmica de las 4 tinas mediante Tiempo Proporcional (Burst Firing) a ciclos completos de 60 Hz en ventanas temporales de 3000 ms gobernado por la librería JELDimmer2. Conmuta exclusivamente en cruce por cero, eliminando de raíz las interferencias electromagnéticas (EMI) sobre el electrodo de pH y los termopares. Incluye perro guardián UART de 4000 ms que corta todas las salidas si se interrumpe la comunicación con el ESP32.'
  },
  max6675: {
    titulo: 'Transmisores Térmicos: 4x MAX6675 SPI @ 4 MHz',
    chip: 'Maxim Integrated / Analog Devices MAX6675ISA',
    pines: 'SCK (GPIO 18), MISO (GPIO 19), CS0-CS3 (GPIO 5, 4, 13, 14)',
    bus: 'SPI Compartido @ 4 MHz con 4 líneas Chip-Select dedicadas',
    desc: 'Digitalizadores con compensación de unión fría integrada para 4 termopares tipo K sumergidos en las tinas de Desengrase, Decapado, Niquelado y Celda Hull. Resolución de 0.25 °C con tiempo de conversión de 0.22 s y detección de termopar abierto.'
  },
  ads1115: {
    titulo: 'ADC de Precisión: ADS1115 16-Bit Sigma-Delta (Canales A0-A1 pH y A2-A3 VCSS)',
    chip: 'Texas Instruments ADS1115IDGSR (Dirección I²C 0x48)',
    pines: 'SDA (GPIO 8), SCL (GPIO 9), Canales A0-A1 (pH Modo Diferencial), Canales A2-A3 (Shunts VCSS Sensado Kelvin)',
    bus: 'I²C Fast-Mode @ 400 kHz con PGA programable (±4.096V) y muestreo continuo a 860 SPS',
    desc: 'Digitalizador analógico de alta precisión operando en modo diferencial. Los Canales A0-A1 están configurados en modo pseudo-diferencial dedicados a la sonda de pH (PH-4502C) para anular desplazamientos de potencial galvánico y ruidos de modo común. Los Canales A2-A3 adquieren en modo diferencial la caída Kelvin sobre los shunts cerámicos (0.50 Ω equivalente) del sumidero VCSS para telemetría continua de corriente y diagnóstico de salud de celda.'
  },
  zcs: {
    titulo: 'Detector de Cruce por Cero Dual (AC 60 Hz / DC 12V)',
    chip: 'Optoacoplador 4N35 / PC817 + Circuito Detector Pasivo',
    pines: 'Entrada AC 127V / 60 Hz ➔ Salida Colector Abierto a INT MCU',
    bus: 'Interrupción Externa por flanco descendente (8.33 ms)',
    desc: 'Detecta el instante exacto en que la senoide de red pasa por 0V. Permite al firmware disparar los TRIACs y conmutar el relé de +12V exclusivamente en el cruce por cero, eliminando picos di/dt, protegiendo los contactos contra arco eléctrico y suprimiendo interferencias EMI sobre la sonda de pH.'
  },
  vcss: {
    titulo: 'Sumidero Lineal VCSS (Voltage-Controlled Current Sink)',
    chip: 'LM358N (Op-Amp Error) + 2x IRLZ44Z MOSFETs + MCP4725 DAC',
    pines: 'Consigna DAC MCP4725 (0-3.53V) ➔ Gate MOSFETs ➔ Cátodo Celda Hull',
    bus: 'Lazo Analógico Ultrarrápido (< 50 µs) + I²C DAC @ 400 kHz',
    desc: 'Circuito sumidero de precisión diseñado bajo la nota técnica Texas Instruments SLAA868A. Regula la densidad de corriente catódica (0 a 3.50 A continuo / pulsado a 10 Hz) hacia la probeta de zincado en la Celda Hull con transconductancia neta de 2.00 A/V y dos shunts cerámicos de 1.0 Ω / 10W.'
  },
  triacs: {
    titulo: 'Módulo de Potencia TRIACs (4 Canales AC)',
    chip: '4x TRIACs BTA24-800BW + 4x Drivers MOC3021',
    pines: 'Disparos optoacoplados de 5V ➔ Puertas TRIAC ➔ Resistencias 450W / 18W',
    bus: 'Conmutación por Tiempo Proporcional (Burst Firing) a 60 Hz en ventanas de 3000 ms',
    desc: 'Etapa de potencia de estado sólido de fabricación propia para controlar la temperatura de las 4 tinas (Desengrase 85-90°C, Decapado 85-90°C, Celda Hull 25/40°C y Niquelado 30-35°C). Conmutación de paquetes de ciclos completos en V=0 sin recorte de fase.'
  },
  rele: {
    titulo: 'Actuador Electromecánico: Módulo de Relés Songle (5V Optoacoplado)',
    chip: 'Songle SRD-05VDC-SL-C + Optoacopladores PC817 + Driver NPN',
    pines: 'Control Lógico Relé VCSS (GPIO 20 Active-LOW), Borneras Salida K1/K2',
    bus: 'Control digital TTL @ 5V con aislamiento galvánico óptico',
    desc: 'Actuador electromecánico de seguridad (10A @ 30VDC). Ejecuta la desconexión física de seguridad del ánodo (+12V DC) sincronizada con cruce por cero (ZCS a corriente nula 0.00 A) para anular el arco voltaico y evitar desgaste de contactos.'
  },
  ph: {
    titulo: 'Sensor de Acidez: Sonda Combinada + Módulo PH-4502C en Modo Diferencial (A0-A1)',
    chip: 'Electrodo Combinado Vidrio-Ag/AgCl + Módulo Transmisor PH-4502C',
    pines: 'Conector coaxial BNC ➔ Señal analógica Po vs Vref ➔ Canales A0-A1 Diferencial ADS1115',
    bus: 'Ultra-Alta Impedancia (> 10¹² Ω) + Conversión I²C Sigma-Delta + Calibración NVS Tri-Modo',
    desc: 'Cadena de medición potenciométrica de pH in-operando en Celda Hull y tinas. Se conecta en modo diferencial entre los Canales A0 y A1 del convertidor ADS1115 a 860 SPS para rechazar bucles de tierra e interferencias galvánicas del baño, con filtrado digital adaptativo IIR en cascada (α = 0.30 en transitorios, α = 0.08 en reposo) y calibración multipunto independiente persistida en Flash NVS.'
  },
  scada: {
    titulo: 'Estación de Supervisión SCADA Telemetría 2.0 (PyQt6 / Python)',
    chip: 'PC Host (Python 3.9+ / PyQt6 / pyqtgraph) + HTTP REST (/data_all)',
    pines: 'Wi-Fi SoftAP "Uli" (192.168.4.1) / USB-CDC Serial @ 115200 Baud',
    bus: 'Protocolo REST JSON (/data_all a 10 Hz) + Polling Asíncrono Resiliente',
    desc: 'Software SCADA industrial de alto nivel bajo norma ISA-88. Gestiona la matriz experimental para 32 probetas desde Excel, ejecuta culombimetría faradaica en lazo cerrado Q = ∫ I dt, modelo bicapa aditivo Zn+Ni, integración con balanza analítica para cálculo automático del rendimiento catódico η% y espesores en micrómetros, y genera automáticamente el paquete de 8 figuras científicas a 300 DPI.'
  }
};

function seleccionarNodoArch(id) {
  const panel = document.getElementById('archDetailPanel');
  const data = ARCH_NODOS[id];
  if (!panel || !data) return;

  document.querySelectorAll('.arch-node').forEach(n => n.classList.remove('active'));
  const el = document.getElementById('node-' + id);
  if (el) el.classList.add('active');

  panel.style.display = 'block';
  panel.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
      <div>
        <strong style="color: #38bdf8; font-size: 0.95rem;">${data.titulo}</strong>
        <div style="color: #94a3b8; font-size: 0.78rem; font-family: var(--code-font); margin-top: 2px;">
          ⚙️ <strong>Componente:</strong> ${data.chip}
        </div>
      </div>
      <button onclick="document.getElementById('archDetailPanel').style.display='none'" style="background: transparent; border: none; color: #94a3b8; font-size: 1.1rem; cursor: pointer;">✕</button>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; margin-top: 10px; font-size: 0.82rem;">
      <div style="background: rgba(0,0,0,0.3); padding: 8px 10px; border-radius: 6px;">
        <span style="color: var(--primary); font-weight: 600;">🔌 Conexión & Pines:</span>
        <div style="color: #cbd5e1; font-family: var(--code-font); font-size: 0.76rem; margin-top: 2px;">${data.pines}</div>
      </div>
      <div style="background: rgba(0,0,0,0.3); padding: 8px 10px; border-radius: 6px;">
        <span style="color: var(--emerald); font-weight: 600;">📡 Bus de Comunicación:</span>
        <div style="color: #cbd5e1; font-family: var(--code-font); font-size: 0.76rem; margin-top: 2px;">${data.bus}</div>
      </div>
    </div>
    <p style="font-size: 0.83rem; color: #e2e8f0; line-height: 1.5; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px;">
      <strong>Función en Planta & Metodología Experimental:</strong> ${data.desc}
    </p>
  `;
}

// =========================================================================
// CONTROLADOR DE MODO DE LECTURA (SHOWCASE EJECUTIVO VS. REPORTE TÉCNICO)
// =========================================================================
let modoLecturaActual = 'showcase';

function setModoLectura(modo) {
  modoLecturaActual = modo;
  document.body.classList.remove('modo-showcase', 'modo-tecnico');
  document.body.classList.add(`modo-${modo}`);

  const btnShowcase = document.getElementById('btnModoShowcase');
  const btnTecnico = document.getElementById('btnModoTecnico');
  if (btnShowcase && btnTecnico) {
    if (modo === 'showcase') {
      btnShowcase.classList.add('active');
      btnTecnico.classList.remove('active');
    } else {
      btnTecnico.classList.add('active');
      btnShowcase.classList.remove('active');
    }
  }

  // Si estamos en modo técnico, asegurar que los acordeones muestren su contenido
  const collapsibleBlocks = document.querySelectorAll('.math-collapsible');
  collapsibleBlocks.forEach(block => {
    if (modo === 'tecnico') {
      block.classList.remove('collapsed');
      const toggleBtn = block.previousElementSibling?.querySelector('.math-toggle-btn') || 
                        block.parentElement?.querySelector('.math-toggle-btn');
      if (toggleBtn) toggleBtn.innerHTML = '🔼 Contraer deducción analítica';
    } else {
      // en modo showcase, replegar si no fue abierto manualmente
      if (!block.dataset.manuallyExpanded) {
        block.classList.add('collapsed');
        const toggleBtn = block.previousElementSibling?.querySelector('.math-toggle-btn') || 
                          block.parentElement?.querySelector('.math-toggle-btn');
        if (toggleBtn) toggleBtn.innerHTML = '📖 Ver deducción analítica paso a paso ▾';
      }
    }
  });

  try {
    localStorage.setItem('cts_modo_lectura', modo);
  } catch (e) {
    // localStorage no disponible o bloqueado en contexto local
  }
}

function toggleMathCollapsible(btn, targetId) {
  const target = document.getElementById(targetId);
  if (!target) return;

  const isCollapsed = target.classList.contains('collapsed');
  if (isCollapsed) {
    target.classList.remove('collapsed');
    target.dataset.manuallyExpanded = 'true';
    btn.innerHTML = '🔼 Contraer deducción analítica';
  } else {
    target.classList.add('collapsed');
    delete target.dataset.manuallyExpanded;
    btn.innerHTML = '📖 Ver deducción analítica paso a paso ▾';
  }
}

// Inicializar modo de lectura al cargar el DOM
document.addEventListener('DOMContentLoaded', () => {
  let modoGuardado = 'showcase';
  try {
    modoGuardado = localStorage.getItem('cts_modo_lectura') || 'showcase';
  } catch (e) {}
  setModoLectura(modoGuardado);

  // Soporte de desplazamiento suave compensado para enlaces de roadmap
  document.querySelectorAll('.roadmap-step').forEach(stepLink => {
    stepLink.addEventListener('click', (e) => {
      const targetHash = stepLink.getAttribute('href');
      if (targetHash && targetHash.startsWith('#')) {
        const elem = document.querySelector(targetHash);
        if (elem) {
          e.preventDefault();
          elem.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });
});

