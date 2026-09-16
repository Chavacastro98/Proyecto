import subprocess
import os

pages = [
    ('web_01_hub.png', 'index.html', '960,860'),
    ('web_02_termico.png', 'termico.html', '960,1220'),
    ('web_03_fuente.png', 'fuente.html', '960,1380'),
    ('web_03_fuente_pulsed.png', 'fuente_pulsado.html', '960,1520'),
    ('web_04_ph.png', 'ph.html', '960,1320'),
    ('web_05_sensores.png', 'sensores.html', '960,1380'),
    ('web_06_consola.png', 'consola.html', '1050,860'),
    ('web_07_update.png', 'update.html', '900,860')
]

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out_dir = r"C:\Proyecto\Proyecto\documentos\imagenes"
preview_dir = r"C:\Proyecto\Proyecto\preview\RTOS2.0"

for name, page, size in pages:
    out_file = os.path.join(out_dir, name)
    url = f"file:///{os.path.join(preview_dir, page).replace(os.sep, '/')}"
    args = [
        chrome_path,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={size}",
        f"--screenshot={out_file}",
        url
    ]
    print(f"Rendering {page} -> {name} ({size})...")
    res = subprocess.run(args, capture_output=True, text=True)
    if os.path.exists(out_file):
        print(f"  OK: {name} ({os.path.getsize(out_file)} bytes)")
    else:
        print(f"  FAIL: {name}")

print("All screenshots successfully captured!")
