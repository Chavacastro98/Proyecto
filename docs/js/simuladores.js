/**
 * Showcase Técnico CTS-C51 | SMEQ 2026
 * SIMULADORES FÍSICOS: Control Térmico ZCS, Fuente Pulsada VCSS (SOA) y Faraday
 */

  // SIMULADOR 1: ZCS TIEMPO PROPORCIONAL
  // =========================================================================
  function actualizarSimuladorTermico() {
    const duty = parseInt(document.getElementById('rngDuty').value, 10);
    const potNom = parseFloat(document.getElementById('rngPotNom').value);
    const tbaseSec = parseInt(document.getElementById('rngTbase').value, 10);

    const totalCiclos = tbaseSec * 60;
    const ciclosActivos = Math.round(totalCiclos * (duty / 100));
    const potEfectiva = potNom * (duty / 100);

    document.getElementById('lblDutyVal').textContent = duty + ' %';
    document.getElementById('lblPotNomVal').textContent = potNom.toFixed(0) + ' W';
    document.getElementById('lblTbaseVal').textContent = tbaseSec.toFixed(1) + ' s (' + totalCiclos + ' ciclos)';

    document.getElementById('valCiclosActivos').textContent = ciclosActivos + ' / ' + totalCiclos;
    document.getElementById('valPotEfectiva').textContent = potEfectiva.toFixed(1) + ' W';

    dibujarOndaZCS(duty, totalCiclos, ciclosActivos);
  }

  function dibujarOndaZCS(duty, totalCiclos, ciclosActivos) {
    const canvas = document.getElementById('canvasZCS');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.offsetWidth;
    const h = canvas.height = 120;

    ctx.clearRect(0, 0, w, h);

    // Eje central
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();

    const ciclosADibujar = Math.min(totalCiclos, 30);
    const ratioActivo = duty / 100;
    const ciclosVerdes = Math.round(ciclosADibujar * ratioActivo);
    const periodoPx = w / ciclosADibujar;

    for (let c = 0; c < ciclosADibujar; c++) {
      const esActivo = c < ciclosVerdes;
      ctx.beginPath();
      ctx.strokeStyle = esActivo ? '#10b981' : '#334155';
      ctx.lineWidth = esActivo ? 2 : 1;

      for (let px = 0; px <= periodoPx; px++) {
        const x = c * periodoPx + px;
        const angle = (px / periodoPx) * 2 * Math.PI;
        const y = h / 2 - Math.sin(angle) * (esActivo ? 42 : 10);
        if (px === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  }

  // =========================================================================
  // SIMULADOR 2: ONDA CUADRADA PULSADA A 10 HZ & VCSS
  // =========================================================================
  let modoCorrienteActual = 'pulsada';

  function setModoCorriente(modo) {
    modoCorrienteActual = modo;
    const btnPulsado = document.getElementById('btnModoPulsado');
    const btnDC = document.getElementById('btnModoDC');
    const lblModo = document.getElementById('lblModoFuente');
    const grpDuty = document.getElementById('grpDutyPulse');

    if (modo === 'pulsada') {
      btnPulsado.classList.add('active');
      btnDC.classList.remove('active');
      lblModo.textContent = 'Pulsada (10 Hz)';
      lblModo.style.color = 'var(--emerald)';
      grpDuty.style.display = 'block';
    } else {
      btnDC.classList.add('active');
      btnPulsado.classList.remove('active');
      lblModo.textContent = 'DC Puro (Continuo)';
      lblModo.style.color = 'var(--primary)';
      grpDuty.style.display = 'none';
    }
    actualizarOndaCuadrada();
  }

  function actualizarOndaCuadrada() {
    const Ipeak = parseFloat(document.getElementById('rngIpeak').value);
    const dutyPercent = parseInt(document.getElementById('rngDutyPulse').value, 10);
    const freq = parseInt(document.getElementById('rngFreqPulse').value, 10);

    const T_ms = 1000 / freq; // Periodo en ms
    const dutyRatio = (modoCorrienteActual === 'pulsada') ? (dutyPercent / 100) : 1.0;
    const Ton_ms = T_ms * dutyRatio;
    const Toff_ms = T_ms - Ton_ms;
    const Iavg = Ipeak * dutyRatio;

    document.getElementById('lblIpeakVal').textContent = Ipeak.toFixed(2) + ' A';
    document.getElementById('lblDutyPulseVal').textContent = dutyPercent + ' % (t_on = ' + Ton_ms.toFixed(1) + ' ms)';
    document.getElementById('lblFreqPulse').textContent = freq + ' Hz (T = ' + T_ms.toFixed(1) + ' ms • ' + freq + ' pulsos/s)';

    document.getElementById('valIavg').textContent = Iavg.toFixed(2) + ' A';
    document.getElementById('valTon').textContent = Ton_ms.toFixed(1) + ' ms';
    document.getElementById('valToff').textContent = (modoCorrienteActual === 'pulsada') ? Toff_ms.toFixed(1) + ' ms' : '0.0 ms';

    dibujarCanvasPulse(Ipeak, Iavg, dutyRatio, freq);
    actualizarCalculadoraVCSS(Ipeak, Iavg);
  }

  function dibujarCanvasPulse(Ipeak, Iavg, dutyRatio, freq) {
    const canvas = document.getElementById('canvasPulse');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.offsetWidth;
    const h = canvas.height = 145;

    ctx.clearRect(0, 0, w, h);

    const padLeft = 45;
    const padRight = 15;
    const padTop = 18;
    const padBottom = 28;
    const drawW = w - padLeft - padRight;
    const drawH = h - padTop - padBottom;

    // Cuadrícula de osciloscopio digital (10 divisiones horizontales de tiempo)
    ctx.strokeStyle = '#0f172a';
    ctx.lineWidth = 1;
    ctx.strokeRect(padLeft, padTop, drawW, drawH);

    // Rejilla de tiempo (divisiones cada 100 ms para ventana de 1000 ms)
    ctx.strokeStyle = 'rgba(30, 41, 59, 0.7)';
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);
    for (let div = 1; div < 10; div++) {
      const gx = padLeft + (drawW * div) / 10;
      ctx.beginPath();
      ctx.moveTo(gx, padTop);
      ctx.lineTo(gx, padTop + drawH);
      ctx.stroke();
    }

    // Rejilla de amplitud (niveles 2A, 4A, 6A)
    for (let currentLevel = 2; currentLevel <= 6; currentLevel += 2) {
      const gy = padTop + drawH * (1 - currentLevel / 7.5);
      ctx.beginPath();
      ctx.moveTo(padLeft, gy);
      ctx.lineTo(padLeft + drawW, gy);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // Eje 0A y posiciones Y de corriente
    const y0 = padTop + drawH;
    const yPeak = padTop + drawH * (1 - Ipeak / 7.5);
    const yAvg = padTop + drawH * (1 - Iavg / 7.5);

    // Etiquetas de corriente (Eje Y)
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px "JetBrains Mono", Consolas, monospace';
    ctx.fillText(Ipeak.toFixed(1) + ' A', 6, Math.max(padTop + 10, yPeak + 4));
    ctx.fillText('0.0 A', 6, y0 + 3);

    // Marcas de tiempo (Eje X: Ventana de observación fija de 1.0 s)
    ctx.fillStyle = '#64748b';
    ctx.font = '9px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('0 ms', padLeft - 2, y0 + 16);
    ctx.fillText('500 ms', padLeft + drawW / 2 - 16, y0 + 16);
    ctx.fillText('1000 ms (1 s)', padLeft + drawW - 55, y0 + 16);

    // Línea de Corriente Media I_avg (discontinua verde esmeralda)
    ctx.beginPath();
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.moveTo(padLeft, yAvg);
    ctx.lineTo(padLeft + drawW, yAvg);
    ctx.stroke();
    ctx.setLineDash([]);

    // Etiqueta I_avg
    ctx.fillStyle = '#10b981';
    ctx.font = 'bold 9px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('I_avg: ' + Iavg.toFixed(2) + ' A', padLeft + drawW - 95, yAvg - 5);

    // CANTIDAD DE PULSOS DINÁMICA SEGÚN LOS HZ CONFIGURADOS:
    // En una ventana de 1.0 s, el número de ciclos completos es exactamente 'freq' (Hz = ciclos/segundo).
    const ciclos = (modoCorrienteActual === 'pulsada') ? Math.max(1, freq) : 1;
    const periodoPx = drawW / ciclos;

    ctx.beginPath();
    ctx.strokeStyle = '#0ea5e9';
    ctx.lineWidth = (ciclos > 15) ? 1.8 : 2.4;

    let currX = padLeft;
    ctx.moveTo(currX, y0);

    if (modoCorrienteActual === 'dc') {
      // Modo DC Puro: nivel constante a I_peak
      ctx.lineTo(currX, yPeak);
      ctx.lineTo(padLeft + drawW, yPeak);
      ctx.lineTo(padLeft + drawW, y0);
      ctx.stroke();

      ctx.lineTo(padLeft, y0);
      ctx.fillStyle = 'rgba(14, 165, 233, 0.14)';
      ctx.fill();
    } else {
      // Modo Pulsado: Se dibujan exactamente 'freq' pulsos a lo largo de la ventana de 1 segundo
      for (let c = 0; c < ciclos; c++) {
        const tonPx = periodoPx * dutyRatio;
        const toffPx = periodoPx * (1 - dutyRatio);

        // Flanco de subida
        ctx.lineTo(currX, yPeak);
        // Nivel alto activo (t_on)
        currX += tonPx;
        ctx.lineTo(currX, yPeak);
        // Flanco de bajada
        ctx.lineTo(currX, y0);
        // Nivel bajo de reposo (t_off)
        currX += toffPx;
        ctx.lineTo(currX, y0);
      }
      ctx.stroke();

      // Relleno sombreado bajo los pulsos
      ctx.lineTo(padLeft + drawW, y0);
      ctx.lineTo(padLeft, y0);
      ctx.fillStyle = 'rgba(14, 165, 233, 0.14)';
      ctx.fill();

      // Marcadores t_on y t_off (se rotulan en el primer pulso si el ancho lo permite)
      if (periodoPx >= 35) {
        const tonMitad = padLeft + (periodoPx * dutyRatio) / 2;
        if (periodoPx * dutyRatio >= 18) {
          ctx.fillStyle = '#38bdf8';
          ctx.font = 'bold 9px "JetBrains Mono", Consolas, monospace';
          ctx.fillText('t_on', tonMitad - 8, yPeak - 5);
        }
        if (dutyRatio < 0.95 && periodoPx * (1 - dutyRatio) >= 18) {
          const toffMitad = padLeft + (periodoPx * dutyRatio) + (periodoPx * (1 - dutyRatio)) / 2;
          ctx.fillStyle = '#94a3b8';
          ctx.font = '9px "JetBrains Mono", Consolas, monospace';
          ctx.fillText('t_off', toffMitad - 10, y0 - 6);
        }
      }
    }
  }

  // CALCULADORA DE BALANCE TÉRMICO VCSS (2 RAMAS CON SHUNT DE 1 Ω / 10W)
  function actualizarCalculadoraVCSS(IpeakVal, IavgVal) {
    const Ipeak = IpeakVal !== undefined ? IpeakVal : parseFloat(document.getElementById('rngIpeak').value);
    const Iavg = IavgVal !== undefined ? IavgVal : (Ipeak * 0.5);

    const Vfuente = parseFloat(document.getElementById('rngVfuente').value);
    const Vcelda = parseFloat(document.getElementById('rngVcelda').value);
    const Theta = parseFloat(document.getElementById('rngTheta').value);

    document.getElementById('lblVfuenteVal').textContent = Vfuente.toFixed(1) + ' V';
    document.getElementById('lblVceldaVal').textContent = Vcelda.toFixed(1) + ' V';
    document.getElementById('lblThetaVal').textContent = Theta.toFixed(1) + ' °C/W';

    // Topología: 2 ramas en paralelo con shunts cerámicos de 1.0 Ω (10W) cada una
    const Rshunt_rama = 1.0;
    const Rshunt_eq = 0.5; // 1.0 Ω || 1.0 Ω
    const I_rama_peak = Ipeak / 2;
    const I_rama_avg = Iavg / 2;

    const Vshunt = Ipeak * Rshunt_eq; // Caída sobre el banco de shunts
    const Vds = Math.max(0, Vfuente - Vcelda - Vshunt);

    // Disipación: 2 MOSFETs IRLZ44Z se reparten equitativamente la corriente
    const Pmosfet_total = Vds * Iavg;
    const Pmosfet_rama = Vds * I_rama_avg; // Potencia disipada en cada MOSFET TO-220

    // Disipación en cada resistencia shunt cerámica de 1 Ω (10W)
    const Pshunt_rama = I_rama_avg * I_rama_avg * Rshunt_rama;

    const Tamb = 25.0;
    const Theta_jc = 0.7; // TO-220 juntura-a-cápsula
    const Theta_cs = 0.5; // Grasa térmica aislante mica
    // El disipador evacúa la potencia total de ambos MOSFETs
    const Tj = Tamb + Pmosfet_rama * (Theta_jc + Theta_cs) + Pmosfet_total * (Theta / 2);

    document.getElementById('valVds').textContent = Vds.toFixed(2) + ' V';
    document.getElementById('valPmosfet').textContent = Pmosfet_rama.toFixed(1) + ' W';
    const elPtotal = document.getElementById('valPmosfetTotal');
    if (elPtotal) elPtotal.textContent = 'Total 2 ramas: ' + Pmosfet_total.toFixed(1) + ' W';
    document.getElementById('valTj').textContent = Tj.toFixed(1) + ' °C';
    document.getElementById('valPshunt').textContent = Pshunt_rama.toFixed(1) + ' W';

    const alertaBox = document.getElementById('boxAlertaSOA');
    if (Tj > 125 || Pmosfet_rama > 40 || Pshunt_rama > 10) {
      alertaBox.className = 'info-box info-box-danger';
      alertaBox.innerHTML = '<strong>PELIGRO DE DESTRUCCIÓN TÉRMICA (SOA / SHUNT EXCEDIDO):</strong><br>La temperatura de unión Tj (' + Tj.toFixed(1) + ' °C) o la potencia en shunt (' + Pshunt_rama.toFixed(1) + ' W > 10 W) superan los límites seguros. Aumenta la ventilación forzada o reduce el voltaje de fuente.';
    } else if (Tj > 90 || Pmosfet_rama > 25 || Pshunt_rama > 7.5) {
      alertaBox.className = 'info-box info-box-warn';
      alertaBox.innerHTML = '<strong>PRECAUCIÓN TÉRMICA:</strong><br>El circuito opera a régimen elevado (Tj = ' + Tj.toFixed(1) + ' °C, P_shunt = ' + Pshunt_rama.toFixed(1) + ' W / 10 W). Se requiere ventilación forzada activa sobre el disipador.';
    } else {
      alertaBox.className = 'info-box info-box-success';
      alertaBox.innerHTML = '<strong>Estado SOA: OPERACIÓN SEGURA (2 RAMAS BALANCEADAS)</strong><br>Ambos transistores operan dentro de su Área de Operación Segura (Tj = ' + Tj.toFixed(1) + ' °C < 90 °C) y los shunts disipan ' + Pshunt_rama.toFixed(1) + ' W por rama (&lt; 10 W nominal).';
    }

    // Actualizar curvas paramétricas y punto Q del IRLZ44N
    actualizarCurvasIRLZ44(I_rama_peak, Vds);
  }

  // =========================================================================
  // SIMULADOR PARAMÉTRICO: CURVAS DEL MOSFET IRLZ44N & TRANSCONDUCTANCIA gm
  // =========================================================================
  let vistaCurvasMosfet = 'vds'; // 'vds' o 'vgs'

  function setVistaCurvasMosfet(vista) {
    vistaCurvasMosfet = vista;
    const btnVds = document.getElementById('btnVistaCurvasVds');
    const btnVgs = document.getElementById('btnVistaCurvasVgs');
    if (btnVds && btnVgs) {
      if (vista === 'vds') {
        btnVds.style.background = 'var(--purple)';
        btnVds.style.color = '#ffffff';
        btnVgs.style.background = 'transparent';
        btnVgs.style.color = '#94a3b8';
      } else {
        btnVgs.style.background = 'var(--purple)';
        btnVgs.style.color = '#ffffff';
        btnVds.style.background = 'transparent';
        btnVds.style.color = '#94a3b8';
      }
    }
    const Ipeak = parseFloat(document.getElementById('rngIpeak').value);
    const Vfuente = parseFloat(document.getElementById('rngVfuente').value);
    const Vcelda = parseFloat(document.getElementById('rngVcelda').value);
    const Vds = Math.max(0, Vfuente - Vcelda - (Ipeak * 0.5));
    actualizarCurvasIRLZ44(Ipeak / 2, Vds);
  }

  function actualizarCurvasIRLZ44(I_rama, Vds) {
    const canvas = document.getElementById('canvasMosfetCurvas');
    if (!canvas) return;

    // Constantes del modelo físico IRLZ44N (HEXFET Logic-Level)
    const Vth = 1.50; // Tensión de umbral [V]
    const Kn = 3.20;  // Parámetro de transconductancia de proceso [A/V²]
    const lambda = 0.015; // Modulación de longitud de canal [V⁻¹]
    const Rs = 1.0;   // Resistor de sensado en Source por rama [Ω]

    // Cálculos de polarización en régimen de saturación activa
    const I_clamp = Math.max(0.01, I_rama);
    const Vov = Math.sqrt((2 * I_clamp) / Kn); // Tensión sobre-umbral (VGS - Vth)
    const Vgs_req = Vth + Vov; // VGS requerida en compuerta
    const Vds_sat = Vov;       // Límite de estrangulamiento de canal
    const gm_intrinseco = Kn * Vov * (1 + lambda * Vds); // gm = dID/dVGS
    const margen_lineal = Vds - Vds_sat; // Margen antes de caer a zona óhmica
    const Vshunt = I_clamp * Rs;
    const Vgate_opamp = Vgs_req + Vshunt; // Salida del Op-Amp LM358N

    // Actualización de Métricas en el Panel
    const elPuntoQ = document.getElementById('valPuntoQ');
    if (elPuntoQ) elPuntoQ.textContent = 'Q(' + Vds.toFixed(2) + 'V, ' + I_clamp.toFixed(2) + 'A)';

    const elRegimen = document.getElementById('valRegimenMosfet');
    const elSubregimen = document.getElementById('valSubregimen');
    const elAlertaMargen = document.getElementById('boxAlertaMargenLineal');

    if (Vds < Vds_sat) {
      if (elRegimen) {
        elRegimen.textContent = 'REGIÓN ÓHMICA / TRIODO';
        elRegimen.style.color = '#ef4444';
      }
      if (elSubregimen) elSubregimen.textContent = 'VDS (' + Vds.toFixed(2) + 'V) < VDS,sat (' + Vds_sat.toFixed(2) + 'V) [Desregulado]';
      if (elAlertaMargen) {
        elAlertaMargen.className = 'info-box info-box-danger';
        elAlertaMargen.innerHTML = '<strong>PELIGRO: MOSFET EN REGIÓN ÓHMICA (PÉRDIDA DE REGULACIÓN)</strong><br>El margen VDS (' + Vds.toFixed(2) + ' V) es menor a la tensión de estrangulamiento (' + Vds_sat.toFixed(2) + ' V). El canal no está estrangulado, el Op-Amp se satura a rail positivo (+5V) y la corriente ya no se puede regular como fuente constante.';
      }
    } else if (margen_lineal < 0.6) {
      if (elRegimen) {
        elRegimen.textContent = 'SATURACIÓN MARGINAL';
        elRegimen.style.color = '#f59e0b';
      }
      if (elSubregimen) elSubregimen.textContent = 'Margen lineal crítico: ΔV = ' + margen_lineal.toFixed(2) + ' V';
      if (elAlertaMargen) {
        elAlertaMargen.className = 'info-box info-box-warn';
        elAlertaMargen.innerHTML = '<strong>PRECAUCIÓN: MARGEN LINEAL ESTRECHO (ΔV = ' + margen_lineal.toFixed(2) + ' V)</strong><br>El transistor opera cerca del codo de saturación. Si la celda aumenta su impedancia o la fuente DC cae, el MOSFET entrará en región óhmica.';
      }
    } else {
      if (elRegimen) {
        elRegimen.textContent = 'SATURACIÓN ACTIVA (PENTODO)';
        elRegimen.style.color = '#10b981';
      }
      if (elSubregimen) elSubregimen.textContent = 'Canal estrangulado VDS (' + Vds.toFixed(2) + 'V) ≥ VDS,sat (' + Vds_sat.toFixed(2) + 'V)';
      if (elAlertaMargen) {
        elAlertaMargen.className = 'info-box info-box-success';
        elAlertaMargen.innerHTML = '<strong>MODO DE SUMIDERO IDEAL GARANTIZADO:</strong><br>El MOSFET opera en la región plana de saturación activa (alta impedancia dinámica ro ≈ ∞). La corriente ID depende únicamente de la consigna analógica comandada y es inmune a fluctuaciones o rizado en la Celda Hull.';
      }
    }

    const elVgs = document.getElementById('valVgsReq');
    if (elVgs) elVgs.textContent = Vgs_req.toFixed(2) + ' V';

    const elGm = document.getElementById('valGmIntrinseco');
    if (elGm) elGm.textContent = gm_intrinseco.toFixed(2) + ' S (A/V)';

    const elVdsSat = document.getElementById('valVdsSat');
    if (elVdsSat) elVdsSat.textContent = Vds_sat.toFixed(2) + ' V';

    const elMargen = document.getElementById('valMargenVds');
    if (elMargen) {
      elMargen.textContent = (margen_lineal >= 0 ? '+' : '') + margen_lineal.toFixed(2) + ' V (' + (margen_lineal >= 1.5 ? 'Óptimo' : margen_lineal >= 0.5 ? 'Aceptable' : 'Crítico') + ')';
      elMargen.style.color = margen_lineal >= 1.5 ? '#10b981' : margen_lineal >= 0.5 ? '#f59e0b' : '#ef4444';
    }

    const elVgate = document.getElementById('valVgateOpamp');
    if (elVgate) elVgate.textContent = Vgate_opamp.toFixed(2) + ' V';

    // Dibujo en Canvas según la vista seleccionada
    if (vistaCurvasMosfet === 'vds') {
      dibujarCurvasSalidaIRLZ44(canvas, I_clamp, Vds, Vgs_req, Vds_sat, Vth, Kn, lambda);
    } else {
      dibujarTransferenciaIRLZ44(canvas, I_clamp, Vds, Vgs_req, gm_intrinseco, Vth, Kn);
    }
  }

  function dibujarCurvasSalidaIRLZ44(canvas, I_Q, Vds_Q, Vgs_Q, Vds_sat, Vth, Kn, lambda) {
    const ctx = canvas.getContext('2d');
    const w = canvas.width = (canvas.offsetWidth && canvas.offsetWidth > 50) ? canvas.offsetWidth : (canvas.parentElement ? canvas.parentElement.offsetWidth : 520) || 520;
    const h = canvas.height = 260;

    ctx.clearRect(0, 0, w, h);

    const padLeft = 45;
    const padRight = 20;
    const padTop = 20;
    const padBottom = 35;
    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    const maxVds = 12.0;
    const maxId = 4.0; // Amperios por rama

    const mapX = (v) => padLeft + (v / maxVds) * plotW;
    const mapY = (i) => padTop + plotH - (i / maxId) * plotH;

    // Fondo oscuro con gradiente
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, '#020617');
    grad.addColorStop(1, '#090d16');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Rejilla de fondo
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for (let v = 2; v <= maxVds; v += 2) {
      ctx.beginPath();
      ctx.moveTo(mapX(v), padTop);
      ctx.lineTo(mapX(v), padTop + plotH);
      ctx.stroke();
    }
    for (let i = 1; i <= maxId; i += 1) {
      ctx.beginPath();
      ctx.moveTo(padLeft, mapY(i));
      ctx.lineTo(padLeft + plotW, mapY(i));
      ctx.stroke();
    }

    // 1. Zona Óhmica Sombreada (a la izquierda de la parábola de estrangulamiento)
    ctx.beginPath();
    ctx.moveTo(mapX(0), mapY(0));
    for (let v = 0; v <= 2.5; v += 0.05) {
      const id_sat = 0.5 * Kn * v * v;
      if (id_sat <= maxId) {
        ctx.lineTo(mapX(v), mapY(id_sat));
      }
    }
    ctx.lineTo(mapX(0), mapY(Math.min(maxId, 0.5 * Kn * 2.5 * 2.5)));
    ctx.closePath();
    ctx.fillStyle = 'rgba(239, 68, 68, 0.08)';
    ctx.fill();

    // Rótulo zona óhmica
    ctx.fillStyle = 'rgba(239, 68, 68, 0.5)';
    ctx.font = 'bold 9px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('ZONA ÓHMICA (TRIODO)', mapX(0.2), mapY(3.5));

    // Rótulo zona saturación activa
    ctx.fillStyle = 'rgba(16, 185, 129, 0.45)';
    ctx.font = 'bold 9px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('ZONA DE SATURACIÓN ACTIVA (MODO FUENTE CONSTANTE)', mapX(3.5), mapY(3.7));

    // 2. Parábola de estrangulamiento (Pinch-off boundary: VDS,sat = VGS - Vth)
    ctx.beginPath();
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    let first = true;
    for (let v = 0; v <= 3.0; v += 0.05) {
      const id_sat = 0.5 * Kn * v * v;
      if (id_sat <= maxId) {
        if (first) { ctx.moveTo(mapX(v), mapY(id_sat)); first = false; }
        else { ctx.lineTo(mapX(v), mapY(id_sat)); }
      }
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Etiqueta de la parábola
    ctx.fillStyle = '#f59e0b';
    ctx.font = 'bold 8.5px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('Límite Estrangulamiento VDS = VGS − Vth', mapX(1.4), mapY(0.5 * Kn * 1.4 * 1.4) - 6);

    // 3. Familia de Curvas ID vs VDS para valores fijos de VGS
    const curvasVgs = [1.8, 2.1, 2.4, 2.7, 3.0];
    curvasVgs.forEach((vgs) => {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
      ctx.lineWidth = 1.2;
      const v_sat = vgs - Vth;
      for (let v = 0; v <= maxVds; v += 0.1) {
        let id_val = 0;
        if (v < v_sat) {
          id_val = Kn * ((vgs - Vth) * v - (v * v) / 2);
        } else {
          id_val = 0.5 * Kn * Math.pow(vgs - Vth, 2) * (1 + lambda * v);
        }
        if (id_val <= maxId) {
          const px = mapX(v);
          const py = mapY(id_val);
          if (v === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
      }
      ctx.stroke();

      // Rotular VGS al final de la curva
      const id_end = 0.5 * Kn * Math.pow(vgs - Vth, 2) * (1 + lambda * (maxVds - 0.5));
      if (id_end <= maxId && id_end >= 0.1) {
        ctx.fillStyle = 'rgba(56, 189, 248, 0.6)';
        ctx.font = '8px "JetBrains Mono", Consolas, monospace';
        ctx.fillText('VGS=' + vgs.toFixed(1) + 'V', mapX(maxVds - 1.2), mapY(id_end) - 4);
      }
    });

    // 4. Curva del VGS actual gobernado por el Op-Amp (Resaltada en cian brillante)
    ctx.beginPath();
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2.5;
    for (let v = 0; v <= maxVds; v += 0.1) {
      let id_val = 0;
      if (v < Vds_sat) {
        id_val = Kn * ((Vgs_Q - Vth) * v - (v * v) / 2);
      } else {
        id_val = 0.5 * Kn * Math.pow(Vgs_Q - Vth, 2) * (1 + lambda * v);
      }
      if (id_val <= maxId) {
        const px = mapX(v);
        const py = mapY(id_val);
        if (v === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
    }
    ctx.stroke();

    // 5. Dibujar el Punto de Operación Quiescente Q(Vds, Id)
    const qX = mapX(Math.min(maxVds, Math.max(0, Vds_Q)));
    const qY = mapY(Math.min(maxId, Math.max(0, I_Q)));

    // Líneas punteadas hacia los ejes
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.moveTo(qX, padTop + plotH);
    ctx.lineTo(qX, qY);
    ctx.lineTo(padLeft, qY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Halo y punto Q
    const qColor = Vds_Q >= Vds_sat ? '#10b981' : '#ef4444';
    ctx.beginPath();
    ctx.fillStyle = qColor === '#10b981' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.3)';
    ctx.arc(qX, qY, 10, 0, 2 * Math.PI);
    ctx.fill();

    ctx.beginPath();
    ctx.fillStyle = qColor;
    ctx.arc(qX, qY, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Rótulo del Punto Q
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 10px "JetBrains Mono", Consolas, monospace';
    const labelQ = 'Q(' + Vds_Q.toFixed(2) + 'V, ' + I_Q.toFixed(2) + 'A)';
    const textWidth = ctx.measureText(labelQ).width;
    const textX = qX + 12 + textWidth > w ? qX - textWidth - 12 : qX + 10;
    const textY = qY - 10 < padTop ? qY + 15 : qY - 8;
    ctx.fillText(labelQ, textX, textY);

    // 6. Ejes cartesianos
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    // Eje Y
    ctx.moveTo(padLeft, padTop);
    ctx.lineTo(padLeft, padTop + plotH);
    // Eje X
    ctx.lineTo(padLeft + plotW, padTop + plotH);
    ctx.stroke();

    // Marcas y números Eje Y (ID en Amperios)
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px "JetBrains Mono", Consolas, monospace';
    ctx.textAlign = 'right';
    for (let i = 0; i <= maxId; i += 1) {
      ctx.fillText(i.toFixed(1), padLeft - 6, mapY(i) + 3);
    }
    // Título Eje Y
    ctx.save();
    ctx.translate(14, padTop + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#cbd5e1';
    ctx.font = 'bold 10px "Inter", sans-serif';
    ctx.fillText('Corriente Drenador ID (A / rama)', 0, 0);
    ctx.restore();

    // Marcas y números Eje X (VDS en Voltios)
    ctx.textAlign = 'center';
    for (let v = 0; v <= maxVds; v += 2) {
      ctx.fillText(v.toFixed(0) + 'V', mapX(v), padTop + plotH + 14);
    }
    // Título Eje X
    ctx.fillStyle = '#cbd5e1';
    ctx.font = 'bold 10px "Inter", sans-serif';
    ctx.fillText('Tensión Drenador-Surtidor VDS (V)', padLeft + plotW / 2, h - 8);

    // Actualizar texto descriptivo bajo el canvas
    const leyenda = document.getElementById('leyendaCurvasMosfet');
    if (leyenda) {
      leyenda.innerHTML = '<span>Línea continua cian: Curva V<sub>GS</sub> comandada (' + Vgs_Q.toFixed(2) + ' V).</span>' +
                          '<span>Parábola ámbar: Límite de estrangulamiento V<sub>DS,sat</sub>.</span>' +
                          '<span style="color:' + qColor + '; font-weight:700;">Punto Q: ' + (Vds_Q >= Vds_sat ? 'Saturación Lineal OK' : 'Colapso Óhmico') + '</span>';
    }
  }

  function dibujarTransferenciaIRLZ44(canvas, I_Q, Vds_Q, Vgs_Q, gm_Q, Vth, Kn) {
    const ctx = canvas.getContext('2d');
    const w = canvas.width = (canvas.offsetWidth && canvas.offsetWidth > 50) ? canvas.offsetWidth : (canvas.parentElement ? canvas.parentElement.offsetWidth : 520) || 520;
    const h = canvas.height = 260;

    ctx.clearRect(0, 0, w, h);

    const padLeft = 45;
    const padRight = 50; // Para el segundo eje Y (gm)
    const padTop = 20;
    const padBottom = 35;
    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    const maxVgs = 3.6; // Voltios
    const maxId = 4.0;  // Amperios
    const maxGm = 6.0;  // Siemens

    const mapX = (vgs) => padLeft + (vgs / maxVgs) * plotW;
    const mapYId = (id) => padTop + plotH - (id / maxId) * plotH;
    const mapYGm = (gm) => padTop + plotH - (gm / maxGm) * plotH;

    // Fondo
    ctx.fillStyle = '#020617';
    ctx.fillRect(0, 0, w, h);

    // Rejilla
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for (let v = 1; v <= maxVgs; v += 0.5) {
      ctx.beginPath();
      ctx.moveTo(mapX(v), padTop);
      ctx.lineTo(mapX(v), padTop + plotH);
      ctx.stroke();
    }
    for (let i = 1; i <= maxId; i += 1) {
      ctx.beginPath();
      ctx.moveTo(padLeft, mapYId(i));
      ctx.lineTo(padLeft + plotW, mapYId(i));
      ctx.stroke();
    }

    // 1. Zona de corte (VGS < Vth) sombreada
    ctx.fillStyle = 'rgba(100, 116, 139, 0.12)';
    ctx.fillRect(mapX(0), padTop, mapX(Vth) - mapX(0), plotH);
    ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
    ctx.font = 'bold 8.5px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('CORTE (VGS < Vth)', mapX(Vth / 2) - 30, mapYId(2.0));

    // Línea vertical en Vth = 1.50V
    ctx.beginPath();
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.moveTo(mapX(Vth), padTop);
    ctx.lineTo(mapX(Vth), padTop + plotH);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#f59e0b';
    ctx.font = 'bold 8.5px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('Vth = 1.50 V', mapX(Vth) + 4, padTop + 14);

    // 2. Curva Cuadrática de Transferencia ID vs VGS (Azul Neón)
    ctx.beginPath();
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2.5;
    let started = false;
    for (let v = 0; v <= maxVgs; v += 0.05) {
      let id_val = 0;
      if (v > Vth) {
        id_val = 0.5 * Kn * Math.pow(v - Vth, 2);
      }
      if (id_val <= maxId) {
        if (!started) { ctx.moveTo(mapX(v), mapYId(id_val)); started = true; }
        else { ctx.lineTo(mapX(v), mapYId(id_val)); }
      }
    }
    ctx.stroke();

    // 3. Curva de Transconductancia gm vs VGS (Línea Verde Esmeralda)
    ctx.beginPath();
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 3]);
    let startedGm = false;
    for (let v = 0; v <= maxVgs; v += 0.05) {
      let gm_val = 0;
      if (v > Vth) {
        gm_val = Kn * (v - Vth);
      }
      if (gm_val <= maxGm) {
        if (!startedGm) { ctx.moveTo(mapX(v), mapYGm(gm_val)); startedGm = true; }
        else { ctx.lineTo(mapX(v), mapYGm(gm_val)); }
      }
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // 4. Marcar el punto de operación actual sobre ID y sobre gm
    const ptX = mapX(Math.min(maxVgs, Math.max(0, Vgs_Q)));
    const ptY_Id = mapYId(Math.min(maxId, Math.max(0, I_Q)));
    const ptY_Gm = mapYGm(Math.min(maxGm, Math.max(0, gm_Q)));

    // Línea vertical punteada del VGS actual
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 2]);
    ctx.moveTo(ptX, padTop + plotH);
    ctx.lineTo(ptX, padTop);
    ctx.stroke();
    ctx.setLineDash([]);

    // Punto en curva ID
    ctx.beginPath();
    ctx.fillStyle = '#38bdf8';
    ctx.arc(ptX, ptY_Id, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Punto en curva gm
    ctx.beginPath();
    ctx.fillStyle = '#10b981';
    ctx.arc(ptX, ptY_Gm, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Rótulos de los puntos
    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 9px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('ID = ' + I_Q.toFixed(2) + ' A', ptX + 8, ptY_Id - 4);

    ctx.fillStyle = '#10b981';
    ctx.font = 'bold 9px "JetBrains Mono", Consolas, monospace';
    ctx.fillText('gm = ' + gm_Q.toFixed(2) + ' S', ptX + 8, ptY_Gm + 12);

    // 5. Ejes
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    // Eje Y izquierdo (ID)
    ctx.moveTo(padLeft, padTop);
    ctx.lineTo(padLeft, padTop + plotH);
    // Eje X
    ctx.lineTo(padLeft + plotW, padTop + plotH);
    // Eje Y derecho (gm)
    ctx.moveTo(padLeft + plotW, padTop);
    ctx.lineTo(padLeft + plotW, padTop + plotH);
    ctx.stroke();

    // Rotulación Eje Y Izquierdo (ID)
    ctx.fillStyle = '#38bdf8';
    ctx.font = '9px "JetBrains Mono", Consolas, monospace';
    ctx.textAlign = 'right';
    for (let i = 0; i <= maxId; i += 1) {
      ctx.fillText(i.toFixed(1) + 'A', padLeft - 6, mapYId(i) + 3);
    }

    // Rotulación Eje Y Derecho (gm)
    ctx.fillStyle = '#10b981';
    ctx.textAlign = 'left';
    for (let g = 0; g <= maxGm; g += 1.5) {
      ctx.fillText(g.toFixed(1) + 'S', padLeft + plotW + 6, mapYGm(g) + 3);
    }

    // Rotulación Eje X (VGS)
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'center';
    for (let v = 0; v <= maxVgs; v += 0.5) {
      ctx.fillText(v.toFixed(1) + 'V', mapX(v), padTop + plotH + 14);
    }

    // Título Eje X
    ctx.fillStyle = '#cbd5e1';
    ctx.font = 'bold 10px "Inter", sans-serif';
    ctx.fillText('Tensión Compuerta-Surtidor VGS (V)', padLeft + plotW / 2, h - 8);

    // Leyenda descriptiva
    const leyenda = document.getElementById('leyendaCurvasMosfet');
    if (leyenda) {
      leyenda.innerHTML = '<span style="color:#38bdf8; font-weight:600;">Línea continua cian: Curva cuadrática ID vs VGS.</span>' +
                          '<span style="color:#10b981; font-weight:600;">Línea discontinua verde: gm = dID/dVGS.</span>' +
                          '<span style="color:#f59e0b; font-weight:600;">Vth = 1.50 V (Umbral Logic-Level).</span>';
    }
  }

  // =========================================================================
  // CALCULADORA 4: CULOMBIMETRÍA DE FARADAY
  // =========================================================================
  function actualizarCalculadoraFaraday() {
    const I = parseFloat(document.getElementById('rngIFaraday').value);
    const t_min = parseFloat(document.getElementById('rngTFaraday').value);
    const Area_cm2 = parseFloat(document.getElementById('rngAreaFaraday').value);
    const Rend = parseFloat(document.getElementById('rngRendFaraday').value) / 100;

    document.getElementById('lblIFaradayVal').textContent = I.toFixed(2) + ' A';
    document.getElementById('lblTFaradayVal').textContent = t_min.toFixed(1) + ' min';
    document.getElementById('lblAreaFaradayVal').textContent = Area_cm2.toFixed(1) + ' cm²';
    document.getElementById('lblRendFaradayVal').textContent = (Rend * 100).toFixed(0) + ' %';

    const t_seg = t_min * 60;
    const Q = I * t_seg;
    const M_Zn = 65.38;
    const n = 2;
    const F = 96485.3;
    const rho_Zn = 7.14;

    const m_teorica_g = (Q * M_Zn) / (n * F) * Rend;
    const m_mg = m_teorica_g * 1000;
    const volumen_cm3 = m_teorica_g / rho_Zn;
    const espesor_cm = volumen_cm3 / Area_cm2;
    const espesor_um = espesor_cm * 10000;

    document.getElementById('valQFaraday').textContent = Q.toFixed(1) + ' C';
    document.getElementById('valMasaFaraday').textContent = m_mg.toFixed(1) + ' mg';
    document.getElementById('valEspesorFaraday').textContent = espesor_um.toFixed(2) + ' µm';
  }
