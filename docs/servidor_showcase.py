#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Local de Demostración y Generador de Código QR
Showcase Técnico CTS-C51 | SMEQ 2026
Autor: Equipo de Instrumentación & Control (Fernando Samayoa & Salvador Castro)

Este script:
1. Detecta la IP local de la computadora en la red Wi-Fi o Ethernet.
2. Inicia un servidor HTTP ligero multi-hilo en el puerto 8000.
3. Genera el código QR en imagen (qr_acceso_movil.png) y lo imprime en la terminal (ASCII).
4. Abre automáticamente el navegador en la PC.
5. Permite que cualquier smartphone (Samsung Galaxy, iPhone, etc.) en el mismo Wi-Fi acceda inmediatamente.
"""

import os
import sys
import socket
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

def obtener_ip_local():
    """Detecta la IP local de la máquina en la red LAN/Wi-Fi."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No envía datos reales a internet, solo determina la interfaz de salida preferida
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def buscar_puerto_libre(puerto_inicial=8000, max_intentos=10):
    """Busca el primer puerto disponible a partir de puerto_inicial."""
    for p in range(puerto_inicial, puerto_inicial + max_intentos):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            resultado = sock.connect_ex(('127.0.0.1', p))
            if resultado != 0:
                return p
    return puerto_inicial

def generar_y_mostrar_qr(url_acceso, output_img="qr_acceso_movil.png"):
    """Genera imagen QR y muestra versión ASCII en la consola si es posible."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=3
        )
        qr.add_data(url_acceso)
        qr.make(fit=True)

        # Guardar imagen PNG de alta definición
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_img)
        print(f"  [OK] Imagen QR guardada como: {output_img}")

        print("\n" + "=" * 65)
        print("  ESCANEA ESTE CÓDIGO QR CON TU SAMSUNG GALAXY / SMARTPHONE:")
        print("=" * 65 + "\n")
        try:
            qr.print_ascii(invert=True)
        except Exception:
            pass
        print("-" * 65)
    except ImportError:
        print("  [AVISO] Biblioteca 'qrcode' no encontrada. Instala con: pip install qrcode[pil]")
        print("  (Aún puedes acceder tecleando la URL directamente en el navegador del teléfono)")

def main():
    # Asegurar que el directorio de trabajo es donde está este script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    ip_local = obtener_ip_local()
    puerto = buscar_puerto_libre(8000)
    url_local = f"http://localhost:{puerto}/index.html"
    url_movil = f"http://{ip_local}:{puerto}/index.html"

    print("\n" + "=" * 65)
    print("   CTS-C51 | SHOWCASE TÉCNICO SMEQ 2026 — SERVIDOR LOCAL")
    print("=" * 65)
    print(f"  Acceso en esta PC:   {url_local}")
    print(f"  Acceso Móvil (Wi-Fi): {url_movil}")
    print("=" * 65 + "\n")

    # Generar y mostrar el código QR para el teléfono
    generar_y_mostrar_qr(url_movil)

    # Abrir el navegador en la PC
    try:
        webbrowser.open(url_local)
    except Exception:
        pass

    class CustomHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            # Headers anti-caché durante el desarrollo para actualización inmediata
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            super().end_headers()

    server_address = ('0.0.0.0', puerto)
    httpd = ThreadingHTTPServer(server_address, CustomHandler)

    print(f"\n  [ACTIVO] Servidor escuchando en http://0.0.0.0:{puerto}")
    print("  Presiona CTRL+C en esta terminal para detener el servidor.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  [DETENIDO] Servidor finalizado con éxito.")
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    main()
