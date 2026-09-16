import re, io, sys

for path in [r'c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html', r'c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md']:
    print(f"=== {path} ===")
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if re.search(r'ets|estrobosc', line, re.IGNORECASE):
                # clean up line for console print
                clean = line.strip().encode('ascii', errors='replace').decode('ascii')
                print(f"  {i+1}: {clean[:100]}")
