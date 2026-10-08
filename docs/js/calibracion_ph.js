/**
 * Showcase Técnico CTS-C51 | SMEQ 2026
 * CALIBRACIÓN DE pH: Modelo de Doble Pendiente Asimétrico (3 Puntos Nernst)
 */

  // CALCULADORA 3: CALIBRACIÓN pH DE DOBLE PENDIENTE (3 PUNTOS ASIMÉTRICOS)
  // =========================================================================
  function actualizarCalculadoraPh() {
    const tempC = parseFloat(document.getElementById('rngTempPh').value);
    const V7 = parseFloat(document.getElementById('rngV7').value);
    const V4 = parseFloat(document.getElementById('rngV4').value);
    const V10 = parseFloat(document.getElementById('rngV10').value);
    const Vin = parseFloat(document.getElementById('rngVinPh').value);

    document.getElementById('lblTempPhVal').textContent = tempC.toFixed(1) + ' °C';
    document.getElementById('lblV7Val').textContent = V7.toFixed(0) + ' mV';
    document.getElementById('lblV4Val').textContent = V4.toFixed(0) + ' mV';
    document.getElementById('lblV10Val').textContent = V10.toFixed(0) + ' mV';
    document.getElementById('lblVinPhVal').textContent = Vin.toFixed(0) + ' mV';

    // 1. Sensibilidad y Pendiente Ácida (pH 4.01 a pH 7.00)
    const deltaV_ac = Math.max(10, V4 - V7);
    const deltaPh_ac = 7.00 - 4.01; // 2.99 pH
    const S_acida = deltaV_ac / deltaPh_ac; // mV / pH
    const m_acida = deltaPh_ac / (deltaV_ac / 1000); // pH / V (RTOS 2.0)

    // 2. Sensibilidad y Pendiente Alcalina (pH 7.00 a pH 10.01)
    const deltaV_ba = Math.max(10, V7 - V10);
    const deltaPh_ba = 10.01 - 7.00; // 3.01 pH
    const S_basica = deltaV_ba / deltaPh_ba; // mV / pH
    const m_basica = deltaPh_ba / (deltaV_ba / 1000); // pH / V (RTOS 2.0)

    // 3. Sensibilidad Nernst Teórica dependiente de T
    const Tk = tempC + 273.15;
    const R = 8.31446;
    const F = 96485.3;
    const S_teorica = (2.302585 * R * Tk / F) * 1000; // mV/pH (59.16 mV/pH @ 25°C)

    // 4. Eficiencia y Salud del Electrodo
    const saludAcida = Math.min(115, Math.max(0, (S_acida / S_teorica) * 100));
    const saludBasica = Math.min(115, Math.max(0, (S_basica / S_teorica) * 100));

    // 5. Transducción In-Operando según Dominio Ácido vs Alcalino
    let phCalculado = 7.00;
    const badge = document.getElementById('badgeDominioPh');

    if (Vin >= V7) {
      // Zona Ácida (V >= V7 => pH <= 7.00)
      phCalculado = 7.00 - ((Vin - V7) / S_acida);
      if (badge) {
        badge.className = 'badge badge-primary';
        badge.textContent = 'DOMINIO ÁCIDO (V ≥ V7)';
      }
    } else {
      // Zona Alcalina (V < V7 => pH > 7.00)
      phCalculado = 7.00 + ((V7 - Vin) / S_basica);
      if (badge) {
        badge.className = 'badge badge-purple';
        badge.textContent = 'DOMINIO ALCALINO (V < V7)';
      }
    }
    phCalculado = Math.max(0.00, Math.min(14.00, phCalculado));

    // Despliegue en interfaz
    document.getElementById('valPhCalculado').textContent = phCalculado.toFixed(2) + ' pH';
    document.getElementById('valPendienteAcida').textContent = S_acida.toFixed(2) + ' mV/pH';
    document.getElementById('valSaludAcida').textContent = 'Salud: ' + saludAcida.toFixed(1) + ' %';
    document.getElementById('valPendienteBasica').textContent = S_basica.toFixed(2) + ' mV/pH';
    document.getElementById('valSaludBasica').textContent = 'Salud: ' + saludBasica.toFixed(1) + ' %';
    document.getElementById('valPendienteTeorica').textContent = S_teorica.toFixed(2) + ' mV/pH';
    document.getElementById('valOffsetPh').textContent = V7.toFixed(0) + ' mV';

    dibujarCurvaNernst(V4, V7, V10, Vin, phCalculado, S_acida, S_basica, S_teorica);
  }

  function dibujarCurvaNernst(V4, V7, V10, Vin, phCalc, S_ac, S_ba, S_teor) {
    const canvas = document.getElementById('canvasNernst');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.offsetWidth;
    const h = canvas.height = 135;

    ctx.clearRect(0, 0, w, h);

    const padLeft = 45;
    const padRight = 20;
    const padTop = 15;
    const padBottom = 22;
    const drawW = w - padLeft - padRight;
    const drawH = h - padTop - padBottom;

    const phMin = 1.0, phMax = 13.0;
    const vMin = 950, vMax = 2450;

    function getX(ph) { return padLeft + ((ph - phMin) / (phMax - phMin)) * drawW; }
    function getY(v) { return (padTop + drawH) - ((v - vMin) / (vMax - vMin)) * drawH; }

    // Fondo y marco
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.strokeRect(padLeft, padTop, drawW, drawH);

    // Retícula y etiquetas de voltaje
    ctx.fillStyle = '#64748b';
    ctx.font = '9px monospace';
    const vSteps = [1100, 1500, 1900, 2300];
    vSteps.forEach(v => {
      const y = getY(v);
      ctx.beginPath();
      ctx.strokeStyle = '#0f172a';
      ctx.moveTo(padLeft, y);
      ctx.lineTo(padLeft + drawW, y);
      ctx.stroke();
      ctx.fillText(v + 'm', 8, y + 3);
    });

    // Líneas verticales para los 3 buffers
    [4.01, 7.00, 10.01].forEach(ph => {
      const x = getX(ph);
      ctx.beginPath();
      ctx.strokeStyle = '#1e293b';
      ctx.setLineDash([2, 4]);
      ctx.moveTo(x, padTop);
      ctx.lineTo(x, padTop + drawH);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillText(ph.toFixed(1), x - 8, h - 6);
    });

    // 1. Curva Teórica Ideal de Nernst (línea punteada gris)
    ctx.beginPath();
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.moveTo(getX(2.0), getY(V7 + S_teor * (7.0 - 2.0)));
    ctx.lineTo(getX(12.0), getY(V7 - S_teor * (12.0 - 7.0)));
    ctx.stroke();
    ctx.setLineDash([]);

    // 2. Curva Bilineal Real: Segmento Ácido (pH 2.0 a 7.00)
    ctx.beginPath();
    ctx.strokeStyle = '#0ea5e9';
    ctx.lineWidth = 2.5;
    ctx.moveTo(getX(2.0), getY(V7 + S_ac * (7.00 - 2.0)));
    ctx.lineTo(getX(7.00), getY(V7));
    ctx.stroke();

    // 3. Curva Bilineal Real: Segmento Básico (pH 7.00 a 12.0)
    ctx.beginPath();
    ctx.strokeStyle = '#a855f7';
    ctx.lineWidth = 2.5;
    ctx.moveTo(getX(7.00), getY(V7));
    ctx.lineTo(getX(12.0), getY(V7 - S_ba * (12.0 - 7.00)));
    ctx.stroke();

    // 4. Marcadores de los 3 Buffers
    // Buffer 4.01 (Ámbar)
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath(); ctx.arc(getX(4.01), getY(V4), 5, 0, 2*Math.PI); ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1; ctx.stroke();

    // Buffer 7.00 (Esmeralda - Vértice Isopotencial)
    ctx.fillStyle = '#10b981';
    ctx.beginPath(); ctx.arc(getX(7.00), getY(V7), 6, 0, 2*Math.PI); ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.5; ctx.stroke();

    // Buffer 10.01 (Rosa / Magenta)
    ctx.fillStyle = '#ec4899';
    ctx.beginPath(); ctx.arc(getX(10.01), getY(V10), 5, 0, 2*Math.PI); ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1; ctx.stroke();

    // 5. Marcador de Lectura en Vivo (Cursor Azul Cielo con proyectores)
    const xLive = getX(phCalc);
    const yLive = getY(Vin);

    // Líneas de proyección punteadas
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
    ctx.setLineDash([2, 2]);
    ctx.moveTo(xLive, padTop + drawH);
    ctx.lineTo(xLive, yLive);
    ctx.lineTo(padLeft, yLive);
    ctx.stroke();
    ctx.setLineDash([]);

    // Punto vivo
    ctx.fillStyle = '#38bdf8';
    ctx.beginPath(); ctx.arc(xLive, yLive, 6, 0, 2*Math.PI); ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.stroke();
  }

  // =========================================================================