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
