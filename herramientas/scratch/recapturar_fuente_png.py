import subprocess
import os

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out_dir = r"c:\Proyecto\Proyecto\documentos\imagenes"
preview_dir = r"c:\Proyecto\Proyecto\preview\RTOS1.3"

out_file = os.path.join(out_dir, "web_03_fuente.png")
url = f"file:///{os.path.join(preview_dir, 'fuente.html').replace(os.sep, '/')}"

args = [
    chrome_path,
    "--headless",
    "--no-sandbox",
    "--disable-gpu",
    "--window-size=960,1050",
    f"--screenshot={out_file}",
    url
]

print(f"Re-capturing fuente.html -> {out_file}...")
res = subprocess.run(args, capture_output=True, text=True)
if os.path.exists(out_file):
    print(f"SUCCESS: web_03_fuente.png re-rendered! Size: {os.path.getsize(out_file)} bytes")
else:
    print("FAILED to re-render web_03_fuente.png")
