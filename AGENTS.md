# Reglas de Formato y Estilo de Respuestas (Antigravity)

## Prohibición Estricta de Sintaxis LaTeX ($ y $$)
El visor de Markdown y la interfaz de chat del IDE no renderizan KaTeX ni MathJax. El uso de delimitadores como `$`, `$$`, `\text{...}`, `\frac{...}`, `\Omega`, `\approx`, etc., se visualiza como texto crudo con barras invertidas y llaves rotas.

### Reglas Obligatorias:
1. **Nunca usar signos de dólar ($ o $$) ni comandos LaTeX:**
   - Prohibido: `$1.5\text{ A}$`, `$\pm 5\%$`, `$\Omega$`, `$$\frac{A}{B}$$`
   - Permitido: `1.5 A`, `±5%`, `Ω`, `A / B`
2. **Usar Caracteres Unicode Directos para Símbolos Matemáticos y Unidades:**
   - Ohm / Resistencia: `Ω`, `mΩ`, `kΩ`
   - Tolerancia / Variación: `±`
   - Aproximación: `≈`
   - Multiplicación: `·` o `x`
   - Temperatura: `°C`
   - Micro: `μ` (ejemplo: `μs`, `μA`)
   - Delta: `Δ` (ejemplo: `Δt`, `ΔR`)
   - Potencias: `I²`, `t²` o `I^2`
3. **Fórmulas y Ecuaciones:**
   Escribir las ecuaciones en formato de texto plano limpio o dentro de bloques de código:
   ```text
   P = I² · R = (1.5)² · 1.0 = 2.25 W
   amplitudDAC = amplitudDAC_Setpoint / factorGananciaVCSS
   ```
