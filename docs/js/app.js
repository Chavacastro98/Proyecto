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
});

window.addEventListener('resize', () => {
  if (typeof actualizarSimuladorTermico === 'function') actualizarSimuladorTermico();
  if (typeof actualizarOndaCuadrada === 'function') actualizarOndaCuadrada();
  if (typeof actualizarCalculadoraPh === 'function') actualizarCalculadoraPh();
});
