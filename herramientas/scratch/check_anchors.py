import re

with open(r'c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html', encoding='utf-8') as f:
    html = f.read()

# Find all IDs
ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
# Find all href="#..."
hrefs = set(re.findall(r'href=["\']#([^"\']+)["\']', html))

missing = hrefs - ids
print(f"Total IDs found: {len(ids)}")
print(f"Total internal links found: {len(hrefs)}")
if missing:
    print(f"WARNING: Missing IDs for links: {missing}")
else:
    print("ALL internal anchor links have valid matching element IDs!")
