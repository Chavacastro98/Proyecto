import re
content = open(r"c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html", encoding="utf-8").read()
titles = re.findall(r'<h2[^>]*>(.*?)</h2>', content)
for i, t in enumerate(titles, 1):
    clean_t = re.sub(r'[^\x00-\x7F]+', '', t).strip()
    print(f"{i}. {clean_t}")
