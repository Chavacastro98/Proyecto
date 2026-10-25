# Guía de Alojamiento y Despliegue — Web Interactiva SMEQ 2026 (CTS-C51)

> **Proyecto:** *Optimización Electroquímica de Recubrimientos de Zinc sobre Aluminio 6061 T-6 mediante Diseño de Experimentos y Control In-Operando*  
> **Congreso:** XLI Congreso Nacional de la Sociedad Mexicana de Electroquímica (SMEQ 2026)  
> **Institución:** CUCEI — Universidad de Guadalajara / Volta Plating Solutions  
> **URL Oficial del QR:** `https://chavacastro98.github.io/Proyecto/`  

---

## 1. Manifiesto de Archivos Requeridos

La aplicación interactiva está diseñada de forma **100% autónoma y ultraligera**, sin frameworks pesados ni dependencias de CDN externas (funciona aun sin internet ni conexión de datos):

| Archivo / Carpeta | Tamaño | Función |
| :--- | :--- | :--- |
| `showcase_web/index.html` | ~42 KB | Aplicación técnica completa: 7 módulos, simulador térmico ZCS a 60 Hz, calculadora analítica VCSS/MOSFET, curva Nernst de pH, integrador Faraday y galería SCADA. |
| `showcase_web/assets/sistema.png` | ~537 KB | Diagrama de bloques de arquitectura de hardware en alta definición con zoom modal. |
| `showcase_web/assets/scada_01_principal.jpg` | ~180 KB | Captura real del panel maestro del SCADA PyQt6 (monitoreo in-operando de las 4 tinas). |
| `showcase_web/assets/scada_02_actuadores.jpg` | ~114 KB | Captura real del esfuerzo de control de actuadores TRIAC y VCSS. |
| `showcase_web/assets/scada_03_errores.jpg` | ~106 KB | Curvas de seguimiento y reducción de errores térmicos en lazo cerrado. |
| `showcase_web/assets/scada_04_faraday.jpg` | ~111 KB | Integración culombimétrica de Faraday y cálculo de espesor de capa de zinc. |
| `showcase_web/assets/scada_05_ph.jpg` | ~120 KB | Curvas dinámicas de estabilización y filtrado de pH. |
| `showcase_web/assets/onda_zcs_tiempo_proporcional.jpg` | ~270 KB | Oscilograma de conmutación por paquetes de ciclos senoidales en cruce por cero (Burst Firing). |
| `showcase_web/assets/metrologia_pulsado_10hz.jpg` | ~154 KB | Metrología del tren de pulsos de corriente a 10 Hz del sumidero VCSS. |
| `showcase_web/assets/estados_isa88.jpg` | ~191 KB | Diagrama de máquina de estados según norma ANSI/ISA-88.01. |
| `showcase_web/assets/circuito_vcss.png` | ~20 KB | Esquemático del sumidero analógico (Op-Amp + MOSFET + Shunt de 0.1 Ω). |
| `showcase_web/assets/placa_conectada.jpg` | ~149 KB | Fotografía del sistema embebido físico en el banco de ensayo. |
| `showcase_web/assets/modulo_triacs.jpg` | ~130 KB | Fotografía del módulo optoacoplado de potencia ZCS. |
| `showcase_web/assets/vcss_placa.jpg` | ~126 KB | Fotografía de la etapa de potencia con transistor disipado. |
| `showcase_web/assets/sensor_ph.jpg` | ~69 KB | Fotografía de la celda de electrodeposición y electrodo compuesto de pH. |
| **Peso Total del Sitio** | **~2.3 MB** | **Carga instantánea (< 150 ms) con cero dependencias externas.** |

> [!IMPORTANT]
> **Política de Confidencialidad y Propiedad Intelectual:**  
> El manuscrito in-extenso (`PLANTILLA-Memoria-extenso-SMEQ26.docx`) **NO está incluido ni referenciado** en la web pública. La web únicamente muestra la cita formal aprobada del cartel y el correo institucional de contacto (`Omar.Gonzalez3420@academicos.udg.mx`) para solicitudes de correspondencia académica.

---

## 2. Hoja Imprimible con Código QR Suelto (Para Mesa del Stand o Cartel)

Para colocar sobre la mesa frente al cartel o pegarlo como apoyo físico adicional:

- **Archivo PDF para imprimir en papel bond blanco (Tamaño Carta / Letter):**  
  [`HOJA_QR_MESA_SMEQ2026.pdf`](../cartel_cientifico/HOJA_QR_MESA_SMEQ2026.pdf)
- **Previsualización de verificación:**  
  [`HOJA_QR_MESA_preview.png`](../cartel_cientifico/HOJA_QR_MESA_preview.png)
- **Script generador:**  
  [`generar_hoja_qr_imprimible.py`](../scripts/generar_hoja_qr_imprimible.py)

---

## 3. Opción A: Demostración desde Laptop / PC *(La Opción Más Fácil y Recomendada)*

Llevar una laptop a la sesión de carteles ofrece **la mejor experiencia visual** para los evaluadores e investigadores:

### Ventajas de usar Laptop:
1. **Doble exhibición:** Puedes tener la web abierta a pantalla completa en la laptop colocada en una mesita o atril frente al cartel, permitiendo que cualquiera interactúe con el simulador SCADA en una pantalla grande.
2. **Servidor local para celulares:** La laptop puede generar su propia red Wi-Fi y servir la web a cualquier asistente que escanee el QR.
3. **Hardware en vivo (Opcional):** Si llevas la placa electrónica, puedes conectar el ESP32-S3 por USB y correr la telemetría real (`launcher.py`).

### Paso a Paso para Servir desde Laptop:
1. Conecta la laptop a la red del congreso o activa el **Hotspot Móvil de Windows** (*Configuración > Red e Internet > Zona con cobertura inalámbrica móvil*).
2. Ve a la carpeta `C:\Proyecto\Proyecto\documentos\academicos\`.
3. Haz doble clic en el archivo:
   ```cmd
   iniciar_servidor_showcase.bat
   ```
4. El script detectará automáticamente tu IP local e iniciará el servidor:
   - **En la laptop:** Se abrirá automáticamente `http://localhost:8080`.
   - **Para celulares en la misma red:** Mostrará la URL directa, por ejemplo `http://192.168.137.1:8080`.

---

## 4. Opción B: Alojamiento desde Samsung Galaxy S26 Ultra *(Plan del Compañero)*

Alojar un servidor web desde un celular Android en un entorno de congreso presenta dos retos técnicos:
1. Las redes Wi-Fi públicas de congresos/hoteles activan **Aislamiento de Clientes (AP Isolation)**, impidiendo que un teléfono se comunique con otro.
2. Los datos móviles (5G/LTE) utilizan **CGNAT** (no permiten conexiones entrantes desde internet).

Para resolver esto en el **Samsung Galaxy S26 Ultra**, disponen de dos métodos probados:

### Método B.1: Hotspot Móvil del Galaxy (100% Offline y Confiable)
Este método no requiere internet ni red del congreso:
1. **Copiar archivos al teléfono:**  
   Pasa la carpeta `showcase_web/` completa al almacenamiento del S26 Ultra (vía cable USB, Samsung Quick Share o Google Drive).
2. **Instalar una app de servidor HTTP:**  
   Desde Google Play Store, descarga **"Simple HTTP Server"** (desarrollador: Ray Adams) o **"KWS Android Web Server"**.
3. **Configuración de la App:**  
   - Selecciona como directorio raíz (`Root Path`) la carpeta `showcase_web`.
   - Puerto: `8080`.
   - Pulsa **Start / Iniciar**.
4. **Activar Zona Wi-Fi en el S26 Ultra:**  
   - Ve a *Ajustes > Conexiones > Mobile Hotspot / Zona Wi-Fi*.
   - Nombre de red: `SMEQ26-Demo` (sin contraseña o con una clave sencilla como `12345678`).
5. **Conexión:**  
   Cualquier persona que se conecte a esa red puede abrir en su navegador `http://192.168.43.1:8080` (IP fija estándar del hotspot de Android).

### Método B.2: Termux con Cloudflare Quick Tunnel (Acceso Remoto vía Datos Móviles)
Si tu compañero quiere que el celular dé servicio a personas con sus propios datos móviles sin conectarse a su hotspot:
1. Instalar **Termux** (desde F-Droid o GitHub).
2. En Termux ejecutar:
   ```bash
   pkg update && pkg install python wget
   cd /sdcard/Download/showcase_web
   python -m http.server 8080 &
   ```
3. Correr el cliente de túnel de Cloudflare:
   ```bash
   pkg install cloudflared
   cloudflared tunnel --url http://localhost:8080
   ```
   Cloudflare generará una URL pública segura `https://xxxx.trycloudflare.com`.

---

## 5. Opción C: GitHub Pages *(La Solución Definitiva y Permanente)*

Esta es la solución más elegante, robusta y profesional:
- **Cero mantenimiento durante el congreso:** No depende de batería, calor del teléfono ni conexiones locales.
- **Acceso universal:** Funciona tanto en el congreso como semanas después cuando los evaluadores revisen el material en sus laboratorios.
- **La URL ya está en el código QR del cartel:** `https://chavacastro98.github.io/Proyecto/`.

### Cómo Publicar la Web en GitHub Pages en 3 Minutos:

Para garantizar que los archivos confidenciales de tu repositorio **NO** se publiquen, el despliegue se realiza a través de la rama aislada `gh-pages`:

Abre PowerShell o CMD en `C:\Proyecto\Proyecto` y ejecuta los siguientes comandos:

```bash
# 1. Asegúrate de estar en la raíz del repositorio
cd C:\Proyecto\ELECTRODO_32

# 2. Crear una rama huérfana limpia llamada gh-pages (sin historial ni archivos fuente)
git checkout --orphan gh-pages

# 3. Vaciar el árbol temporal de git
git rm -rf .

# 4. Copiar únicamente los archivos de la web interactiva a la raíz
xcopy /s /e /y documentos\academicos\showcase_web\* .

# 5. Agregar y confirmar los archivos web
git add index.html assets/
git commit -m "Publicar Showcase Web Interactivo SMEQ 2026 v2.0"

# 6. Subir la rama a GitHub
git push -u origin gh-pages --force

# 7. Regresar a tu rama de trabajo principal
git checkout main
```

#### Paso Final en la Web de GitHub:
1. Entra a tu repositorio: `https://github.com/Chavacastro98/Proyecto`
2. Ve a **Settings** > **Pages** (en el menú lateral izquierdo).
3. En **Build and deployment**:
   - **Source:** Selecciona `Deploy from a branch`.
   - **Branch:** Selecciona `gh-pages` y carpeta `/ (root)`.
   - Clic en **Save**.
4. En aproximadamente 60 segundos, tu página estará activa en:  
   👉 **`https://chavacastro98.github.io/Proyecto/`**

---

## 6. Verificación del Cartel con Código QR

El código QR fue incrustado con precisión milimétrica en el cartel oficial:

- **Archivo PDF listo para imprenta:**  
  [`DOC-20261004-WA0001_con_QR.pdf`](DOC-20261004-WA0001_con_QR.pdf)
- **Imagen del QR de alta resolución (300 DPI):**  
  [`codigo_qr_cartel.png`](../cartel_cientifico/codigo_qr_cartel.png)
- **Previsualización de verificación:**  
  [`cartel_con_qr_preview.png`](../cartel_cientifico/cartel_con_qr_preview.png)
