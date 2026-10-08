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

// MODAL DE IMÁGENES / LIGHTBOX HD
function abrirModal(src, titulo) {
  const modal = document.getElementById('modalOverlay');
  const modalImg = document.getElementById('modalImg');
  const modalTitle = document.getElementById('modalTitle');
  if (!modal || !modalImg) return;
  modalImg.src = src;
  if (modalTitle) modalTitle.textContent = titulo || 'Inspección en Alta Resolución';
  modal.classList.add('open');
}

function cerrarModal(e) {
  if (e && e.target && e.target !== e.currentTarget && !e.target.classList.contains('modal-close')) return;
  const modal = document.getElementById('modalOverlay');
  if (modal) modal.classList.remove('open');
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const modal = document.getElementById('modalOverlay');
    if (modal) modal.classList.remove('open');
  }
});

// INICIALIZACIÓN GLOBAL
window.addEventListener('DOMContentLoaded', () => {
  if (typeof actualizarSimuladorTermico === 'function') actualizarSimuladorTermico();
  if (typeof actualizarOndaCuadrada === 'function') actualizarOndaCuadrada();
  if (typeof actualizarCalculadoraPh === 'function') actualizarCalculadoraPh();
  if (typeof actualizarCalculadoraFaraday === 'function') actualizarCalculadoraFaraday();
  if (typeof seleccionarNodoArch === 'function') seleccionarNodoArch('esp32');
});

window.addEventListener('resize', () => {
  if (typeof actualizarSimuladorTermico === 'function') actualizarSimuladorTermico();
  if (typeof actualizarOndaCuadrada === 'function') actualizarOndaCuadrada();
  if (typeof actualizarCalculadoraPh === 'function') actualizarCalculadoraPh();
});

// CONTROLADOR DEL DIAGRAMA DE ARQUITECTURA VECTORIAL INTERACTIVO
const ARCH_NODOS = {
  esp32: {
    titulo: 'Master: ESP32-S3 N16R8 Dual-Core @ 240 MHz',
    chip: 'Espressif Systems ESP32-S3-WROOM-1',
    pines: 'Dual Core LX7, 512KB SRAM, 8MB PSRAM Octal, 16MB Flash SPI',
    bus: 'Coordinador Maestro: I²C Fast-Mode (GPIO 8/9), SPI @ 4MHz (GPIO 10-13), UART2 (GPIO 17)',
    desc: 'Núcleo central del sistema. Core 0 ejecuta FreeRTOS con servidor HTTP asíncrono, WebSockets para telemetría a 10 Hz y gestión Wi-Fi SoftAP. Core 1 ejecuta en tiempo real determinístico los 4 lazos de control PI térmicos, muestreo ADC, supervisión del sumidero VCSS y la máquina de estados secuencial ISA-88.'
  },
  nano: {
    titulo: 'Esclavo: Arduino Nano Coprocesador @ 16 MHz',
    chip: 'ATmega328P / Microchip',
    pines: 'D2 (INT0 ZCS), D3-D6 (Gate TRIACs), D1 (TX UART), D0 (RX UART)',
    bus: 'UART2 Esclavo @ 9600 Baud + Interrupción externa INT0 / INT1',
    desc: 'Coprocesador dedicado exclusivamente al control de fase y conmutación de los 4 TRIACs de potencia. Descarga al ESP32 de interrupciones críticas de microsegundos de la red eléctrica de 60 Hz e incorpora Watchdog Fail-Safe de 3.0 s por desconexión de bus.'
  },
  max6675: {
    titulo: 'Transmisores Térmicos: 4x MAX6675 SPI @ 4 MHz',
    chip: 'Maxim Integrated / Analog Devices MAX6675ISA',
    pines: 'SCK (GPIO 12), MISO (GPIO 13), CS0-CS3 (GPIO 10, 11, 14, 15)',
    bus: 'SPI Compartido @ 4 MHz con 4 líneas Chip-Select dedicadas',
    desc: 'Digitalizadores con compensación de unión fría integrada para 4 termopares tipo K sumergidos en las tinas de Desengrase, Decapado, Niquelado y Celda Hull. Resolución de 0.25 °C con tiempo de conversión de 0.22 s y detección de termopar abierto.'
  },
  ads1115: {
    titulo: 'ADC de Precisión: ADS1115 16-Bit Sigma-Delta',
    chip: 'Texas Instruments ADS1115IDGSR (Dirección I²C 0x48)',
    pines: 'SDA (GPIO 8), SCL (GPIO 9), Canales A0-A1 (pH), A2-A3 (Shunts)',
    bus: 'I²C Fast-Mode @ 400 kHz con PGA programable (±0.256V a ±6.144V)',
    desc: 'Digitalizador analógico diferencial de alta resolución. Los canales A0-A1 adquieren la señal analógica del módulo PH-4502C en modo pseudo-diferencial con cancelación de modo común, y los canales A2-A3 leen la caída de tensión en el banco de shunts cerámicos de 1.0 Ω del VCSS.'
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
    pines: 'Consigna DAC MCP4725 (0-3.3V) ➔ Gate MOSFETs ➔ Cátodo Celda Hull',
    bus: 'Lazo Analógico Ultrarrápido (< 50 µs) + I²C DAC @ 400 kHz',
    desc: 'Circuito sumidero de precisión diseñado bajo la nota técnica Texas Instruments SLAA868A. Regula la densidad de corriente catódica (0 a 6.6 A) hacia la probeta de zincado en la Celda Hull con transconductancia neta de 2 A/V y compensación capacitiva de compuerta R_ISO = 100 Ω.'
  },
  triacs: {
    titulo: 'Módulo de Potencia TRIACs MDAC4C (4 Canales AC)',
    chip: '4x TRIACs BTA24-600B (25A / 600V) + 4x Drivers MOC3021',
    pines: 'Disparos optoacoplados de 5V ➔ Puertas TRIAC ➔ Resistencias 450W',
    bus: 'Conmutación por Tiempo Proporcional (Burst Firing) a 60 Hz',
    desc: 'Etapa de potencia de estado sólido para controlar la temperatura de las 4 tinas industriales (Desengrase 90°C, Decapado 90°C, Niquelado 30°C y Celda Hull 30°C). Conmutación de paquetes de ciclos completos en V=0 sin recorte de fase.'
  },
  scada: {
    titulo: 'Estación de Supervisión SCADA PyQt6 & Servidor Web',
    chip: 'PC Host (Python 3.14 / PyQt6 / pyqtgraph) + WebSockets / HTTP',
    pines: 'Puerto COM USB-CDC @ 115200 Baud / Conexión Wi-Fi 802.11 b/g/n',
    bus: 'Protocolo de Tramas Binarias + REST API JSON',
    desc: 'Software de supervisión de alto nivel. Gestiona la secuencia automatizada de los 32 ensayos Taguchi (DoE 2⁵·4), registra curvas térmicas y de densidad de corriente a 10 Hz, exporta tablas CSV validadas y permite control remoto desde laptops o smartphones Samsung Galaxy S26 Ultra.'
  }
};

function mostrarVistaArquitectura(modo) {
  const btnVec = document.getElementById('btnArchVec');
  const btnImg = document.getElementById('btnArchImg');
  const vistaVec = document.getElementById('vistaArchVectorial');
  const vistaImg = document.getElementById('vistaArchImagen');

  if (modo === 'vectorial') {
    if (btnVec) btnVec.classList.add('active');
    if (btnImg) btnImg.classList.remove('active');
    if (vistaVec) vistaVec.style.display = 'block';
    if (vistaImg) vistaImg.style.display = 'none';
  } else {
    if (btnVec) btnVec.classList.remove('active');
    if (btnImg) btnImg.classList.add('active');
    if (vistaVec) vistaVec.style.display = 'none';
    if (vistaImg) vistaImg.style.display = 'block';
  }
}

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
