import re

with open(r'c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html', encoding='utf-8') as f:
    for i, line in enumerate(f):
        m = re.findall(r'src=["\']([^"\']+\.png)["\']', line)
        if m:
            print(f'{i+1}: {m}')
