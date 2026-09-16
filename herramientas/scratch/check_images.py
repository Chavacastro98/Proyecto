import os
import re

html_path = r"c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

imgs = re.findall(r'src=["\']([^"\']+)["\']', content)
print(f"Total images referenced in HTML: {len(imgs)}")
for img in imgs:
    full = os.path.join(r"c:\Proyecto\Proyecto\documentos", img)
    if os.path.exists(full):
        print(f"  [OK IMG] {img} ({os.path.getsize(full):,} bytes)")
    else:
        print(f"  [MISSING IMG] {img}")

pdfs = re.findall(r'href=["\'](datasheets/[^"\']+)["\']', content)
print(f"\nTotal datasheets referenced in HTML: {len(pdfs)}")
for pdf in pdfs:
    full = os.path.join(r"c:\Proyecto\Proyecto\documentos", pdf)
    if os.path.exists(full):
        print(f"  [OK PDF] {pdf} ({os.path.getsize(full):,} bytes)")
    else:
        print(f"  [MISSING PDF] {pdf}")
