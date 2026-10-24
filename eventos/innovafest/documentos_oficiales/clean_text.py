import re

path = r"C:\Proyecto\Proyecto\Innovafest\01_DOCUMENTO_OFICIAL_POSTULACION.md"

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Exact phrase fixes
text = text.replace(r"($Al_2O_3$)", "(Al₂O₃)")
text = text.replace(r"$Al_2O_3$", "Al₂O₃")
text = text.replace(r"($80–95\ ^\circC$)", "(80–95 °C)")
text = text.replace(r"($85–90\ ^\circC$, 240 s)", "(85–90 °C, 240 s)")
text = text.replace(r"($Na_3PO_4 + Na_2SiO_3 + PEG-400$)", "(Na₃PO₄ + Na₂SiO₃ + PEG-400)")
text = text.replace(r"($85–90\ ^\circC$, 120 s)", "(85–90 °C, 120 s)")
text = text.replace(r"($25\ ^\circC$ o $40\ ^\circC$, $1.50 A$)", "(25 °C o 40 °C, 1.50 A)")
text = text.replace(r"($10 Hz$, 20% ciclo de trabajo)", "(10 Hz, 20% ciclo de trabajo)")
text = text.replace(r"($30–40\ ^\circC$, 600 s)", "(30–40 °C, 600 s)")
text = text.replace(r"($2 × IRFZ44N$ con $R_{shunt} = 1\ Ω$)", "(2× MOSFET IRFZ44N con R_shunt = 1 Ω)")
text = text.replace(r"($10 Hz$, 20% duty cycle, $1.50 A$ pico medidos en osciloscopio con sonda de $10 mV/A$)", "(10 Hz, 20% duty cycle, 1.50 A pico medidos en osciloscopio con sonda de 10 mV/A)")
text = text.replace(r"($MgO$)", "(MgO)")
text = text.replace(r"($MgO$/borosilicato)", "(MgO/borosilicato)")
text = text.replace(r"($± 8\ ^\circC$)", "(±8 °C)")
text = text.replace(r"($± 0.8\ ^\circC$)", "(±0.8 °C)")
text = text.replace(r"$2^5 × 4$", "2⁵ × 4")
text = text.replace(r"($2^5 × 4$)", "(2⁵ × 4)")
text = text.replace(r"(sonda $10 mV/A$)", "(sonda de 10 mV/A)")
text = text.replace(r"$1.50 A$ a $10 Hz$", "1.50 A a 10 Hz")
text = text.replace(r"($20\%$ ciclo útil)", "(20% ciclo útil)")
text = text.replace(r"$± 0.8\ ^\circC$", "±0.8 °C")

# Generic cleanup for any remaining stray LaTeX
text = re.sub(r'\\?\^\\?circ\s*C', '°C', text)
text = re.sub(r'\\?\^\\?circ', '°', text)
text = re.sub(r'\\\s+', ' ', text)

# Remove stray dollars that are not part of money (keep $15,000, $80,000, etc.)
lines = text.splitlines()
cleaned_lines = []
for l in lines:
    # If line is table row with money like "$15,000 MXN", keep it
    # Replace single non-money $
    parts = re.split(r'(\$\d[\d,]*\b)', l)
    new_parts = []
    for p in parts:
        if re.match(r'^\$\d[\d,]*\b', p):
            new_parts.append(p)
        else:
            new_parts.append(p.replace('$', ''))
    cleaned_lines.append(''.join(new_parts))

text = '\n'.join(cleaned_lines)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("SUCCESS: Cleaned 01_DOCUMENTO_OFICIAL_POSTULACION.md")
