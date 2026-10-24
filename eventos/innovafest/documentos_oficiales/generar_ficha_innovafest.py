import os
import io
import base64
import qrcode
from playwright.sync_api import sync_playwright

# Generar código QR hacia https://chavacastro98.github.io/Proyecto/
qr_url = "https://chavacastro98.github.io/Proyecto/"
qr = qrcode.QRCode(
    version=2,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=2,
)
qr.add_data(qr_url)
qr.make(fit=True)
qr_img = qr.make_image(fill_color="#012249", back_color="#ffffff")

buf = io.BytesIO()
qr_img.save(buf, format="PNG")
qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,600&display=swap');

    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    body {{
        width: 900px;
        height: 1280px;
        font-family: 'Montserrat', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background: #002b5e;
        overflow: hidden;
        position: relative;
        color: #ffffff;
        -webkit-font-smoothing: antialiased;
    }}

    /* Fondo con gradientes idénticos a las Fichas Innovafest 2026 */
    .card-bg {{
        width: 100%;
        height: 100%;
        position: relative;
        background:
            radial-gradient(ellipse 68% 48% at 72% 38%, rgba(28, 125, 196, 0.75) 0%, rgba(8, 72, 135, 0.38) 52%, rgba(0, 28, 61, 0) 100%),
            radial-gradient(ellipse 60% 40% at 62% 14%, rgba(35, 138, 212, 0.58) 0%, rgba(0, 45, 92, 0) 75%),
            radial-gradient(ellipse 80% 55% at 20% 85%, rgba(0, 18, 42, 0.94) 0%, rgba(0, 32, 68, 0.4) 65%, transparent 100%),
            linear-gradient(165deg, #044a8f 0%, #02356b 38%, #012249 75%, #011836 100%);
        padding: 26px 28px;
    }}

    /* Marco interior blanco fino */
    .inner-frame {{
        width: 100%;
        height: 100%;
        border: 2px solid rgba(255, 255, 255, 0.88);
        position: relative;
        padding: 36px 48px 32px 48px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}

    /* Etiqueta blanca superior derecha */
    .category-ribbon {{
        position: absolute;
        top: 24px;
        right: 0;
        width: 445px;
        height: 46px;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: -4px 4px 12px rgba(0, 0, 0, 0.25);
        z-index: 5;
    }}

    .category-ribbon span {{
        color: #0d5ea6;
        font-size: 23px;
        font-weight: 700;
        letter-spacing: 0.2px;
    }}

    /* Cabecera: Icono + Título + Subtítulo */
    .header-section {{
        display: flex;
        align-items: center;
        margin-top: 52px;
        gap: 26px;
    }}

    .header-icon {{
        width: 142px;
        min-width: 142px;
        height: 148px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .header-titles {{
        flex: 1;
    }}

    .main-title {{
        font-size: 34px;
        font-weight: 800;
        line-height: 1.13;
        color: #ffffff;
        letter-spacing: 0.2px;
        /* Sombra negra pronunciada estilo Innovafest */
        text-shadow:
            5px 6px 6px rgba(0, 0, 0, 0.95),
            3px 4px 1px rgba(0, 0, 0, 0.9),
            7px 9px 14px rgba(0, 0, 0, 0.8);
        margin-bottom: 10px;
    }}

    .subtitle {{
        font-size: 18px;
        font-weight: 400;
        line-height: 1.28;
        color: #e6f2ff;
        letter-spacing: 0.1px;
    }}

    /* Cuerpo de secciones */
    .body-content {{
        display: flex;
        flex-direction: column;
        gap: 17px;
        margin-top: 14px;
        z-index: 3;
    }}

    .section-block {{
        display: flex;
        flex-direction: column;
    }}

    .section-title {{
        font-size: 21px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 5px;
        letter-spacing: 0.15px;
    }}

    .section-text {{
        font-size: 15.6px;
        font-weight: 400;
        line-height: 1.35;
        color: #dceaf7;
    }}

    .bullet-list {{
        list-style: none;
        padding-left: 16px;
    }}

    .bullet-list li {{
        position: relative;
        padding-left: 15px;
        font-size: 15.5px;
        font-weight: 400;
        line-height: 1.34;
        color: #dceaf7;
        margin-bottom: 3.5px;
    }}

    .bullet-list li::before {{
        content: "•";
        position: absolute;
        left: 0;
        top: 0;
        color: #ffffff;
        font-weight: 700;
    }}

    /* Contenedor inferior: Autores a la izquierda + QR a la derecha */
    .bottom-row {{
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        margin-top: 8px;
        position: relative;
        z-index: 4;
        gap: 20px;
    }}

    .footer-section {{
        flex: 1;
    }}

    .footer-heading {{
        font-size: 15px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.28;
        letter-spacing: 0.1px;
    }}

    .footer-center {{
        font-size: 14.6px;
        font-weight: 700;
        color: #cbe6ff;
        margin-bottom: 9px;
        line-height: 1.28;
        letter-spacing: 0.1px;
    }}

    .author-group {{
        margin-bottom: 7px;
        line-height: 1.26;
    }}

    .author-group:last-child {{
        margin-bottom: 0;
    }}

    .author-name {{
        font-size: 14.3px;
        font-style: italic;
        font-weight: 400;
        color: #e2effc;
    }}

    .author-dept {{
        font-size: 14.3px;
        font-weight: 700;
        color: #ffffff;
    }}

    /* Tarjeta de Código QR */
    .qr-card {{
        display: flex;
        flex-direction: column;
        align-items: center;
        background: rgba(1, 28, 60, 0.72);
        border: 1.5px solid rgba(125, 200, 255, 0.55);
        border-radius: 12px;
        padding: 10px 12px 8px 12px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45);
        min-width: 148px;
    }}

    .qr-box {{
        background: #ffffff;
        padding: 5px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .qr-box img {{
        width: 116px;
        height: 116px;
        display: block;
    }}

    .qr-caption {{
        margin-top: 6px;
        font-size: 11.2px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }}

    .qr-sub {{
        font-size: 9.8px;
        font-weight: 500;
        color: #b8dcff;
        text-align: center;
        margin-top: 1px;
    }}

    /* Marca de agua técnica desplazada sutilmente detrás del QR */
    .watermark-icon {{
        position: absolute;
        bottom: 120px;
        right: -14px;
        width: 175px;
        height: 210px;
        opacity: 0.18;
        z-index: 1;
        pointer-events: none;
    }}
</style>
</head>
<body>
    <div class="card-bg">
        <div class="inner-frame">
            <!-- Cinta de Categoría -->
            <div class="category-ribbon">
                <span>Industria 4.0 y Automatización</span>
            </div>

            <div>
                <!-- Encabezado con Icono + Título -->
                <div class="header-section">
                    <div class="header-icon">
                        <!-- Icono vectorial blanco de celda electroquímica automatizada y control -->
                        <svg viewBox="0 0 140 150" width="140" height="148" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <!-- Nodos superiores de control digital / pulso PWM -->
                            <path d="M22 20 H40 V8 H58 V20 H72" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                            <circle cx="95" cy="14" r="6" stroke="#FFFFFF" stroke-width="4"/>
                            <circle cx="118" cy="14" r="6" stroke="#FFFFFF" stroke-width="4"/>
                            <!-- Cables hacia electrodos -->
                            <path d="M45 28 V48" stroke="#FFFFFF" stroke-width="4.2" stroke-linecap="round"/>
                            <path d="M95 20 V48" stroke="#FFFFFF" stroke-width="4.2" stroke-linecap="round"/>
                            <!-- Tapa / soporte de celda -->
                            <rect x="20" y="46" width="100" height="10" rx="5" stroke="#FFFFFF" stroke-width="4.2"/>
                            <!-- Cuba electrolítica / Celda Hull -->
                            <path d="M26 56 V118 C26 126 32 132 40 132 H100 C108 132 114 126 114 118 V56" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <!-- Nivel de electrolito (onda suave) -->
                            <path d="M28 74 Q48 68 70 74 T112 74" stroke="#FFFFFF" stroke-width="3.6" stroke-linecap="round"/>
                            <!-- Ánodo y Cátodo inmersos -->
                            <rect x="39" y="56" width="12" height="54" rx="2" stroke="#FFFFFF" stroke-width="4"/>
                            <rect x="89" y="56" width="12" height="54" rx="2" stroke="#FFFFFF" stroke-width="4"/>
                            <!-- Flujo iónico / deposición galvánica -->
                            <path d="M58 86 H78 M73 81 L79 86 L73 91" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M58 102 H78 M73 97 L79 102 L73 107" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <!-- Burbujas / reacción -->
                            <circle cx="65" cy="65" r="3" fill="#FFFFFF"/>
                            <circle cx="77" cy="63" r="2.5" fill="#FFFFFF"/>
                            <!-- Base de plataforma instrumentada -->
                            <path d="M16 142 H124" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div class="header-titles">
                        <div class="main-title">
                            Sistema de control<br>automático de recubrimientos<br>electrolíticos
                        </div>
                        <div class="subtitle">
                            Automatización accesible para procesos<br>de galvanoplastia de alta precisión
                        </div>
                    </div>
                </div>

                <!-- Bloques de contenido -->
                <div class="body-content">
                    <div class="section-block">
                        <div class="section-title">Breve descripción</div>
                        <p class="section-text">
                            Planta piloto automatizada que integra control electrónico e instrumentación química para realizar recubrimientos metálicos (zinc y níquel sobre aluminio) de forma sencilla y repetible. Su diseño controla automáticamente las etapas de limpieza, activación y electrodeposición, logrando acabados uniformes, adherentes y sin errores manuales.
                        </p>
                    </div>

                    <div class="section-block">
                        <div class="section-title">Beneficios principales</div>
                        <ul class="bullet-list">
                            <li>Estandarización de todo el proceso para obtener recubrimientos uniformes y con excelente adherencia.</li>
                            <li>Control automático de temperatura, tiempo y corriente eléctrica, con medición continua de pH.</li>
                            <li>Reducción en el desperdicio de reactivos químicos y energía al evitar sobrecalentamientos.</li>
                            <li>Operación cómoda y segura desde celular o computadora mediante conexión inalámbrica (Wi-Fi).</li>
                            <li>Apagado automático de seguridad al finalizar cada etapa del tratamiento.</li>
                        </ul>
                    </div>

                    <div class="section-block">
                        <div class="section-title">Tecnología diferenciadora</div>
                        <ul class="bullet-list">
                            <li>Aplicación de corriente continua y corriente pulsada para mejorar el acabado del metal.</li>
                            <li>Integración de múltiples sensores (temperatura, pH, corriente y voltaje) en un solo sistema.</li>
                            <li>Monitoreo y control en tiempo real desde interfaz web móvil y software en computadora.</li>
                            <li>Registro automático de datos y gráficas para validar y mejorar recetas químicas.</li>
                        </ul>
                    </div>

                    <div class="section-block">
                        <div class="section-title">Ventajas competitivas</div>
                        <ul class="bullet-list">
                            <li>Mayor calidad y repetibilidad en las piezas comparado con los métodos manuales tradicionales.</li>
                            <li>Fabricación económica y accesible frente a maquinaria industrial importada de alto costo.</li>
                            <li>Diseño modular y de fácil mantenimiento utilizando componentes disponibles en el mercado local.</li>
                            <li>Adaptable tanto para laboratorios de enseñanza e investigación como para talleres de galvanoplastia.</li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Pie de página: Autores a la izquierda y QR a la derecha -->
            <div class="bottom-row">
                <div class="footer-section">
                    <div class="footer-heading">Innovación desarrollada en la Universidad de Guadalajara</div>
                    <div class="footer-center">Centro Universitario de Ciencias Exactas e Ingenierías (CUCEI)</div>

                    <div class="author-group">
                        <div class="author-name">Salvador Castro Pérez</div>
                        <div class="author-dept">Departamento de Ingeniería Electro-Fotónica</div>
                    </div>

                    <div class="author-group">
                        <div class="author-name">Fernando Salvador Samayoa Martínez</div>
                        <div class="author-dept">Departamento de Ingeniería Electro-Fotónica</div>
                    </div>

                    <div class="author-group">
                        <div class="author-name">Víctor Ulises Gutiérrez Ramírez</div>
                        <div class="author-dept">Departamento de Ingeniería Química</div>
                    </div>
                </div>

                <div class="qr-card">
                    <div class="qr-box">
                        <img src="data:image/png;base64,{qr_b64}" alt="QR Proyecto Web">
                    </div>
                    <div class="qr-caption">Sitio Web Interactivo</div>
                    <div class="qr-sub">Escanea para explorar</div>
                </div>
            </div>

            <!-- Ilustración marca de agua sutil -->
            <svg class="watermark-icon" viewBox="0 0 200 240" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="42" y="75" width="116" height="125" rx="14" stroke="#4fb3ff" stroke-width="3.5"/>
                <line x1="42" y1="108" x2="158" y2="108" stroke="#4fb3ff" stroke-width="2.5" stroke-dasharray="6 4"/>
                <rect x="64" y="50" width="18" height="110" rx="4" stroke="#4fb3ff" stroke-width="3.5"/>
                <rect x="118" y="50" width="18" height="110" rx="4" stroke="#4fb3ff" stroke-width="3.5"/>
                <path d="M73 50 V22 L52 10" stroke="#4fb3ff" stroke-width="3" stroke-linecap="round"/>
                <circle cx="48" cy="8" r="5" stroke="#4fb3ff" stroke-width="3"/>
                <path d="M127 50 V22 L148 10" stroke="#4fb3ff" stroke-width="3" stroke-linecap="round"/>
                <circle cx="152" cy="8" r="5" stroke="#4fb3ff" stroke-width="3"/>
                <rect x="82" y="138" width="36" height="36" rx="6" stroke="#4fb3ff" stroke-width="3"/>
                <circle cx="100" cy="156" r="8" stroke="#4fb3ff" stroke-width="2.5"/>
            </svg>
        </div>
    </div>
</body>
</html>
"""

out_dir = r"C:\Proyecto\Proyecto\Innovafest"
artifact_dir = r"C:\Users\salva\.gemini\antigravity\brain\511825ca-a2c7-4f44-8b63-de74d8cf484a"

html_path = os.path.join(out_dir, "ficha_innovafest_2026.html")
png_path = os.path.join(out_dir, "Ficha_Innovafest_2026_ELECTRODO32.png")
jpg_path = os.path.join(out_dir, "Ficha_Innovafest_2026_ELECTRODO32.jpg")
pdf_path = os.path.join(out_dir, "Ficha_Innovafest_2026_ELECTRODO32.pdf")
artifact_png = os.path.join(artifact_dir, "Ficha_Innovafest_2026_ELECTRODO32.png")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 900, "height": 1280}, device_scale_factor=2)
    page.goto(f"file:///{html_path.replace(os.sep, '/')}", wait_until="networkidle")
    page.screenshot(path=png_path, type="png")
    page.screenshot(path=jpg_path, type="jpeg", quality=95)
    page.screenshot(path=artifact_png, type="png")
    page.pdf(
        path=pdf_path,
        width="900px",
        height="1280px",
        print_background=True,
        margin={"top": "0px", "bottom": "0px", "left": "0px", "right": "0px"}
    )
    browser.close()

print("SUCCESS:", png_path)
