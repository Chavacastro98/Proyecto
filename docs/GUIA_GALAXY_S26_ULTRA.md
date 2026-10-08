# 📱 Guía de Despliegue en Samsung Galaxy S26 Ultra

**Para:** Fernando Salvador Samayoa Martínez  
**Proyecto:** Showcase Técnico CTS-C51 | SMEQ 2026  
**Dispositivo Principal:** Samsung Galaxy S26 Ultra (Android 16 / One UI 8.x)

---

## ⚡ 1. Cómo pasar el paquete al Galaxy S26 Ultra (3.5 MB)

El archivo comprimido listo para transferir está en:
📁 `documentos/academicos/showcase_web_galaxy_s26_ultra.zip`

Puedes transferirlo a tu teléfono mediante:
- **Samsung Quick Share:** Clic derecho en Windows -> *Compartir con Quick Share* -> Enviar directo a tu Galaxy S26 Ultra.
- **Cable USB-C:** Conecta el teléfono a la laptop/PC y cópialo a la carpeta `Descargas` (`Download`).
- **Google Drive / WhatsApp Web / Telegram:** Envíate el archivo `.zip`.

En tu Galaxy: Abre la app **Mis Archivos** -> Carpeta **Descargas** -> Toca el archivo `.zip` y presiona **Extraer**.

---

## 🚀 2. Opción A: Abrir Directamente en el Teléfono (Sin Servidor)

No necesitas instalar absolutamente nada para ver y utilizar todo el showcase:

1. En la app **Mis Archivos** de tu Galaxy, entra a la carpeta extraída `showcase_web/`.
2. Toca el archivo:
   ```text
   showcase_galaxy_standalone.html
   ```
3. Selecciónalo para abrir con **Samsung Internet** o **Google Chrome**.
4. **¡Listo!** El showcase cargará al instante:
   - 100% Offline (sin gastar datos móviles).
   - Estilos oscuros optimizados para la pantalla Dynamic AMOLED 2X.
   - Pestañas táctiles fluidas con scroll horizontal.
   - Simuladores interactivos de Faraday, VCSS y pH funcionando en tiempo real.
   - Galería fotográfica de placas físicas en alta resolución con zoom táctil.

---

## 📡 3. Opción B: Convertir el Galaxy S26 Ultra en Servidor Web Local (Para que otros escaneen tu QR)

Si estás en el congreso y quieres que los asesores, jurados o asistentes escaneen un código QR desde **tu propio Galaxy S26 Ultra** para ver la web en sus celulares:

### Método 1 (El más rápido desde Google Play Store — 1 Minuto):
1. Instala en tu Galaxy la app gratuita **"Simple HTTP Server"** (de *PhobosSoft*) o **"AWebServer"** desde la Google Play Store.
2. Abre la app y presiona **Choose Folder** (Seleccionar carpeta) -> Elige la carpeta `showcase_web`.
3. Activa el botón **Start / Iniciar**.
4. La app te mostrará una dirección IP (por ejemplo `http://192.168.1.XX:8080`) y un **código QR en la pantalla de tu Galaxy**.
5. Los demás apuntan su cámara a la pantalla de tu teléfono y navegan directamente en la web alojada en tu Galaxy S26 Ultra.

### Método 2 (Para modo Ingeniero con Termux):
Si tienes o instalas **Termux** en tu Galaxy:
```bash
# Instalar python si no lo tienes
pkg install python -y

# Dar permisos de almacenamiento
termux-setup-storage

# Entrar a la carpeta descargada
cd ~/storage/downloads/showcase_web

# Ejecutar el servidor con QR incluido
python servidor_showcase.py
```
El script detectará la IP de tu teléfono y dibujará el código QR en la pantalla de Termux.

---

## 🖥️ 4. Proyección en Cañón o Monitor con Samsung DeX

Tu **Galaxy S26 Ultra** cuenta con la tecnología **Samsung DeX**:

1. Conecta tu teléfono mediante un cable **USB-C a HDMI** (o adaptador multipuerto) al proyector o cañón del congreso.
2. Tu Galaxy activará automáticamente el modo de escritorio **DeX**.
3. Abre **Samsung Internet** o **Chrome** en la pantalla del cañón y arrastra el archivo `index.html` o abre la URL local.
4. Puedes usar la pantalla de tu Galaxy como **Touchpad (ratón táctil)** para cambiar entre pestañas y mover los sliders interactivos ante la audiencia, sin necesidad de cargar una computadora portátil.

---

## 📂 Archivos incluidos en el paquete:

- `showcase_galaxy_standalone.html` → Versión unificada infalible para abrir directo en Android.
- `index.html` → Versión modular para servidores web / GitHub Pages.
- `qr_acceso_movil.png` → Imagen del código QR para mostrar o imprimir.
- `servidor_showcase.py` → Servidor en Python (compatible con PC y Termux Android).
- `iniciar_servidor.bat` → Lanzador para cuando use PC.
- `css/` y `js/` → Módulos divididos de diseño y cálculo.
- `assets/` → Todas las fotografías reales de las placas físicas sin anotaciones.
