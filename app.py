import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import requests
import re
import unicodedata
import hashlib
import json
import urllib.parse
import os
import csv

st.set_page_config(
    page_title="Noticias de Argentina | Dólar, Política, Economía y Deportes en vivo",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== METADATOS SEO / OPEN GRAPH ==========
# Nota: Streamlit renderiza del lado del cliente, así que esto ayuda a redes sociales
# y a buscadores que ejecutan JS, pero no reemplaza un <head> estático servido por el
# servidor. Para SEO más serio (sitemap.xml, robots.txt, meta por URL) conviene, más
# adelante, un frontend estático o SSR delante de esta app.
components.html("""
<script>
try {
    const doc = window.parent.document;
    doc.title = "Noticias de Argentina | Dólar, Política, Economía y Deportes en vivo";
    const metas = [
        {name: "description", content: "Noticias de Argentina en vivo: dólar blue y oficial, riesgo país, política, economía, tabla de la Liga Profesional AFA, clima y toda la actualidad del país, actualizada todo el día."},
        {name: "keywords", content: "noticias argentina, dolar blue hoy, dolar oficial, riesgo pais, tabla afa, liga profesional, politica argentina, economia argentina"},
        {property: "og:title", content: "Noticias de Argentina | Todo el país, en vivo"},
        {property: "og:description", content: "Dólar, riesgo país, política, economía, deportes y clima de Argentina, actualizado en vivo."},
        {property: "og:type", content: "website"},
    ];
    metas.forEach(m => {
        const tag = doc.createElement('meta');
        Object.keys(m).forEach(k => tag.setAttribute(k, m[k]));
        doc.head.appendChild(tag);
    });
} catch (e) {}
</script>
""", height=0, width=0)

# ========== ESTILO DIARIO CLARO ==========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #f7f5f0;
    color: #1a1a1a;
}

.stApp { background-color: #f7f5f0; }

.stApp, .stApp p, .stApp span, .stApp li, .stApp label, .stApp div,
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p, .stCheckbox label p,
[data-testid="stDateInput"] label p {
    color: #1a1a1a;
}

h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #111 !important;
}

/* Sidebar más angosto */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e2db;
    width: 235px !important;
    min-width: 235px !important;
    max-width: 235px !important;
}
section[data-testid="stSidebar"] > div { width: 235px !important; }
[data-testid="stSidebarUserContent"] { padding: 1rem 0.9rem !important; }
section[data-testid="stSidebar"] * { color: #1a1a1a !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #111 !important; font-size: 1.1rem !important; }
section[data-testid="stSidebar"] .stCheckbox { margin-bottom: -8px; }

[data-testid="stDateInput"] input {
    color: #1a1a1a !important;
    background: #ffffff !important;
}

.stButton > button {
    background: #1a1a1a !important;
    color: white !important;
    border-radius: 4px !important;
    border: none !important;
}
.stButton > button p { color: white !important; }

a { color: #8B0000 !important; }
hr { border-color: #ddd !important; }

.noticia-card {
    background: white;
    border: 1px solid #e5e2db;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 14px;
    transition: box-shadow .15s ease, transform .15s ease;
}
.noticia-card:hover {
    box-shadow: 0 6px 16px rgba(11,46,79,.10);
    transform: translateY(-1px);
}

.logo-badge {
    width: 110px;
    height: 75px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 15px;
    text-align: center;
    line-height: 1.15;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.mercado-box {
    background: white;
    border: 1px solid #e5e2db;
    border-radius: 6px;
    padding: 9px 12px;
    margin-bottom: 7px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Botón de compartir por WhatsApp: selector con más especificidad que "a" para que gane siempre */
a.btn-whatsapp, a.btn-whatsapp * {
    color: #ffffff !important;
    text-decoration: none !important;
}
a.btn-whatsapp {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #22B858;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .2px;
    margin-top: 8px;
    box-shadow: 0 2px 5px rgba(34,184,88,.35);
    transition: background .15s ease;
}
a.btn-whatsapp:hover { background: #1DA851; }

/* Pestañas (tabs) más prolijas, para Zona A / Zona B, etc. */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    background: #f0ede4;
    border-radius: 6px 6px 0 0;
    padding: 8px 18px;
    font-weight: 600;
    color: #555 !important;
}
.stTabs [aria-selected="true"] {
    background: #0B2E4F !important;
    color: #ffffff !important;
}
.stTabs [aria-selected="true"] p { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ========== SOL DE MAYO (logo) ==========
def sol_de_mayo_svg(size=48, color="#EFA400", borde="#B8860B"):
    rayos = ""
    for i in range(16):
        ang = i * (360 / 16)
        rayos += f'<rect x="47" y="1" width="6" height="24" rx="1.5" fill="{color}" transform="rotate({ang} 50 50)"></rect>'
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        {rayos}
        <circle cx="50" cy="50" r="23" fill="{color}" stroke="{borde}" stroke-width="2"/>
    </svg>'''

_DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def _fecha_larga_es(dt) -> str:
    return f"{_DIAS_ES[dt.weekday()]} {dt.day} de {_MESES_ES[dt.month - 1]} de {dt.year}"

st.markdown(f"""
<div style="background:linear-gradient(120deg,#0B2E4F 0%,#1B4F91 55%,#2F8FB0 100%);
            border-radius:12px;padding:22px 28px;margin-bottom:8px;
            display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px;
            box-shadow:0 6px 18px rgba(11,46,79,.25);">
    <div style="display:flex;align-items:center;gap:16px;">
        {sol_de_mayo_svg(52)}
        <div>
            <div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:800;color:#fff;line-height:1.05;">
                Noticias de Argentina
            </div>
            <div style="font-size:12px;color:#cfe0f2;letter-spacing:.8px;margin-top:5px;font-weight:600;">
                INFORMACIÓN AL INSTANTE · LAS 24 HORAS
            </div>
        </div>
    </div>
    <div style="text-align:right;">
        <div style="display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.16);
                    padding:5px 14px;border-radius:999px;margin-bottom:7px;">
            <span style="width:8px;height:8px;background:#FF4D4D;border-radius:50%;display:inline-block;
                        animation:pulso-vivo 1.3s ease-in-out infinite;"></span>
            <span style="color:#fff;font-size:11px;font-weight:800;letter-spacing:.6px;">EN VIVO</span>
        </div>
        <div style="color:#e8f1fb;font-size:13px;text-transform:capitalize;">{_fecha_larga_es(datetime.now())}</div>
    </div>
</div>
<style>
@keyframes pulso-vivo {{
    0% {{ opacity:1; transform:scale(1); }}
    50% {{ opacity:.35; transform:scale(1.3); }}
    100% {{ opacity:1; transform:scale(1); }}
}}
</style>
""", unsafe_allow_html=True)


# ========== LOGOS / COLORES DE MEDIOS ==========
LOGOS = {
    "TN": {"color": "#00a0e3", "texto": "TN"},
    "Infobae": {"color": "#e63946", "texto": "INFOBAE"},
    "Cadena 3": {"color": "#1a73e8", "texto": "C3"},
    "La Nación": {"color": "#2b2b2b", "texto": "LA NACIÓN"},
    "Clarín": {"color": "#c8102e", "texto": "CLARÍN"},
    "Olé": {"color": "#ff6600", "texto": "OLÉ"},
    "Infodefensa": {"color": "#2c3e50", "texto": "INFODEFENSA"},
}

PALETA_MEDIOS = [
    "#0F5C97", "#B5482A", "#2F6F4E", "#7A3B69", "#B08900",
    "#374B8C", "#8C3B3B", "#2E7D6B", "#5B4B8A", "#A2572B", "#1B6E8C", "#6E7A2B"
]

def get_logo_html(medio: str) -> str:
    for k, v in LOGOS.items():
        if k.lower() in medio.lower():
            return f'<div class="logo-badge" style="background:{v["color"]};">{v["texto"]}</div>'
    return f'<div class="logo-badge" style="background:#132038;">{sol_de_mayo_svg(46)}</div>'

def color_para_medio(nombre: str) -> str:
    for k, v in LOGOS.items():
        if k.lower() in nombre.lower():
            return v["color"]
    idx = int(hashlib.md5(nombre.encode("utf-8")).hexdigest(), 16) % len(PALETA_MEDIOS)
    return PALETA_MEDIOS[idx]

def _oscurecer(hex_color: str, factor: float = 0.7) -> str:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#333333"
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

def chip_medio(nombre: str) -> str:
    color = color_para_medio(nombre)
    oscuro = _oscurecer(color)
    return (f'<span style="display:inline-block;background:linear-gradient(135deg,{color},{oscuro});'
            f'color:#ffffff;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:700;'
            f'letter-spacing:.5px;box-shadow:0 2px 4px rgba(0,0,0,.20);font-family:Inter,sans-serif;">'
            f'{nombre.upper()}</span>')

def boton_whatsapp(titulo: str, link: str) -> str:
    texto = urllib.parse.quote(f"{titulo} {link}")
    url_wa = f"https://wa.me/?text={texto}"
    return (
        f'<a href="{url_wa}" target="_blank" class="btn-whatsapp">'
        f'<svg width="12" height="12" viewBox="0 0 24 24" fill="white"><path d="M17.6 6.3A8.9 8.9 0 0 0 3.6 17l-1.1 4 4.1-1.1A9 9 0 1 0 17.6 6.3zM12 19.5a7.4 7.4 0 0 1-3.8-1l-.3-.2-2.5.7.7-2.4-.2-.3a7.5 7.5 0 1 1 6.1 3.2zm4.1-5.6c-.2-.1-1.3-.6-1.5-.7-.2-.1-.4-.1-.5.1l-.7.9c-.1.2-.3.2-.5.1a6.1 6.1 0 0 1-3-2.6c-.2-.3.2-.3.5-.9.1-.1.1-.3 0-.4l-.7-1.6c-.2-.4-.4-.4-.5-.4h-.5c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 2s.8 2.3 1 2.5c.1.1 1.7 2.6 4.1 3.6.6.2 1 .4 1.4.5.6.2 1.1.1 1.5.1.5-.1 1.3-.5 1.5-1 .2-.5.2-.9.1-1z"/></svg>'
        f'Compartir</a>'
    )

# ========== BANNER ==========
@st.cache_data(ttl=300)
def obtener_titulares_infobae():
    try:
        feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
        return [{"titulo": e.title, "link": e.link} for e in feed.entries[:7]]
    except Exception:
        return [{"titulo": "Cargando titulares...", "link": "https://www.infobae.com"}]

_titulares_infobae = obtener_titulares_infobae()
texto_banner = "  •  ".join(t["titulo"] for t in _titulares_infobae)
st.markdown(f"""
<div style="background:#111; color:#f5f0e6; padding:9px 0; font-size:13px; overflow:hidden; white-space:nowrap;">
    <div style="display:inline-block; padding-left:100%; animation: marquee 42s linear infinite;">
        INFOBAE HOY · {texto_banner}
    </div>
</div>
<style>@keyframes marquee {{0%{{transform:translateX(0)}}100%{{transform:translateX(-100%)}}}}</style>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== LO MÁS LEÍDO (sidebar) ==========
st.sidebar.markdown("---")
st.sidebar.header("🔥 Tendencias ahora")
for i, t in enumerate(_titulares_infobae[:6], start=1):
    st.sidebar.markdown(
        f'<div style="font-size:12px;margin-bottom:8px;line-height:1.35;">'
        f'<b style="color:#B8860B;">{i}.</b> '
        f'<a href="{t["link"]}" target="_blank" style="color:#1a1a1a!important;text-decoration:none;">{t["titulo"]}</a>'
        f'</div>',
        unsafe_allow_html=True
    )

# ========== RANGO DE FECHAS (fijo, sin selector visible) ==========
fecha_desde = datetime.now().date() - timedelta(days=3)
fecha_hasta = datetime.now().date()

# ========== SIDEBAR ==========
if st.sidebar.button("🔄 Actualizar", use_container_width=True):
    st.rerun()
st.sidebar.header("Categorías")
categorias = {
    "Política": st.sidebar.checkbox("Política", True),
    "Economía": st.sidebar.checkbox("Economía", True),
    "Defensa / Seguridad": st.sidebar.checkbox("Defensa / Seguridad", True),
    "Entretenimiento": st.sidebar.checkbox("Entretenimiento"),
    "Debate / Opinión": st.sidebar.checkbox("Debate / Opinión"),
    "Sociedad": st.sidebar.checkbox("Sociedad"),
    "Internacional": st.sidebar.checkbox("Internacional"),
    "Deportes": st.sidebar.checkbox("Deportes"),
}
categorias_activas = [c for c, v in categorias.items() if v]

# ========== DIARIOS POR PROVINCIA (2 por provincia) ==========
PROVINCIA_MEDIOS = {
    "Buenos Aires": [("El Día", "eldia.com"), ("Diario Hoy", "diariohoy.net")],
    "Ciudad Autónoma de Buenos Aires": [("Clarín", "clarin.com"), ("La Nación", "lanacion.com.ar")],
    "Catamarca": [("El Ancasti", "elancasti.com.ar"), ("El Esquiú", "elesquiu.com")],
    "Chaco": [("Diario Norte", "diarionorte.com"), ("Chaco Día por Día", "chacodiapordia.com")],
    "Chubut": [("El Chubut", "diarioelchubut.com"), ("Jornada", "jornadaonline.com")],
    "Córdoba": [("Cadena 3", "cadena3.com"), ("La Voz del Interior", "lavoz.com.ar")],
    "Corrientes": [("Corrientes Hoy", "corrienteshoy.com"), ("Época", "diarioepoca.com")],
    "Entre Ríos": [("El Diario", "eldiaonline.com"), ("Uno Entre Ríos", "unoentrerios.com.ar")],
    "Formosa": [("La Mañana de Formosa", "lmformosa.com.ar"), ("Diario Textual", "textualformosa.com.ar")],
    "Jujuy": [("Pregón", "pregon.com.ar"), ("Todo Jujuy", "todojujuy.com")],
    "La Pampa": [("La Arena", "laarena.com.ar"), ("El Diario", "eldiariodelapampa.com")],
    "La Rioja": [("El Independiente", "elindependiente.com.ar"), ("Nueva Rioja", "nuevarioja.com.ar")],
    "Mendoza": [("Los Andes", "losandes.com.ar"), ("MDZ Online", "mdzol.com")],
    "Misiones": [("El Territorio", "elterritorio.com.ar"), ("Primera Edición", "primeraedicion.com.ar")],
    "Neuquén": [("LM Neuquén", "lmneuquen.com"), ("Río Negro", "rionegro.com.ar")],
    "Río Negro": [("Río Negro", "rionegro.com.ar"), ("ADN Sur", "adnsur.com.ar")],
    "Salta": [("El Tribuno", "eltribuno.com"), ("El Intransigente", "elintransigente.com")],
    "San Juan": [("Diario de Cuyo", "diariodecuyo.com.ar"), ("Tiempo de San Juan", "tiempodesanjuan.com")],
    "San Luis": [("El Diario de la República", "eldiariodelarepublica.com"), ("Puntal", "puntal.com.ar")],
    "Santa Cruz": [("La Opinión Austral", "laopinionaustral.com.ar"), ("Tiempo Sur", "tiemposur.com.ar")],
    "Santa Fe": [("El Litoral", "ellitoral.com"), ("La Capital", "lacapital.com.ar")],
    "Santiago del Estero": [("El Liberal", "elliberal.com.ar"), ("Nuevo Diario", "nuevodiarioweb.com.ar")],
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur": [("El Sureño", "elsureno.com.ar"), ("Provincia 23", "provincia23.com.ar"), ("InfoFueguina", "infofueguina.com")],
    "Tucumán": [("La Gaceta", "lagaceta.com.ar"), ("Contexto Tucumán", "contextotucuman.com")],
}

# ========== MAPA POLÍTICO: GOBERNADORES ==========
COLOR_PARTIDO = {"peronismo": "#C0392B", "radical": "#6E1B14", "lla": "#8E44AD", "pro": "#F1C40F", "otro": "#8C97A6"}

GOBERNADORES = {
    "Buenos Aires": {"nombre": "Axel Kicillof", "partido": "Unión por la Patria (peronismo)", "color": "peronismo",
                     "resultado": [("Kicillof (UP)", 44.8), ("Grindetti (JxC)", 26.7), ("Píparo (LLA)", 24.6)]},
    "Ciudad Autónoma de Buenos Aires": {"nombre": "Jorge Macri", "partido": "PRO", "color": "pro",
                     "resultado": [("Macri (PRO)", 49.7), ("Santoro (UP)", 32.3)]},
    "Catamarca": {"nombre": "Raúl Jalil", "partido": "Unión por la Patria (PJ)", "color": "peronismo", "resultado": None},
    "Chaco": {"nombre": "Leandro Zdero", "partido": "UCR (Juntos por el Cambio)", "color": "radical", "resultado": None},
    "Chubut": {"nombre": "Ignacio Torres", "partido": "PRO", "color": "pro", "resultado": None},
    "Córdoba": {"nombre": "Martín Llaryora", "partido": "PJ (Hacemos Unidos por Córdoba)", "color": "peronismo", "resultado": None},
    "Corrientes": {"nombre": "Juan Pablo Valdés", "partido": "UCR (Vamos Corrientes)", "color": "radical",
                     "resultado": [("Valdés (Vamos Corrientes)", 51.9), ("Ascúa (Fuerza Patria)", 20.1), ("Colombi", 16.8)]},
    "Entre Ríos": {"nombre": "Rogelio Frigerio", "partido": "PRO", "color": "pro", "resultado": None},
    "Formosa": {"nombre": "Gildo Insfrán", "partido": "Unión por la Patria (PJ)", "color": "peronismo", "resultado": None},
    "Jujuy": {"nombre": "Carlos Sadir", "partido": "UCR", "color": "radical", "resultado": None},
    "La Pampa": {"nombre": "Sergio Ziliotto", "partido": "Unión por la Patria (PJ)", "color": "peronismo", "resultado": None},
    "La Rioja": {"nombre": "Ricardo Quintela", "partido": "Unión por la Patria (PJ)", "color": "peronismo", "resultado": None},
    "Mendoza": {"nombre": "Alfredo Cornejo", "partido": "UCR", "color": "radical", "resultado": None},
    "Misiones": {"nombre": "Hugo Passalacqua", "partido": "Frente Renovador de la Concordia (partido provincial)", "color": "otro", "resultado": None},
    "Neuquén": {"nombre": "Rolando Figueroa", "partido": "Comunidad (partido provincial)", "color": "otro", "resultado": None},
    "Río Negro": {"nombre": "Alberto Weretilneck", "partido": "Juntos Somos Río Negro (partido provincial)", "color": "otro", "resultado": None},
    "Salta": {"nombre": "Gustavo Sáenz", "partido": "Partido de la Victoria (partido provincial)", "color": "otro", "resultado": None},
    "San Juan": {"nombre": "Marcelo Orrego", "partido": "Producción y Trabajo (partido provincial)", "color": "otro", "resultado": None},
    "San Luis": {"nombre": "Claudio Poggi", "partido": "Ahora San Luis (partido provincial)", "color": "otro", "resultado": None},
    "Santa Cruz": {"nombre": "Claudio Vidal", "partido": "SER (partido provincial)", "color": "otro", "resultado": None},
    "Santa Fe": {"nombre": "Maximiliano Pullaro", "partido": "UCR", "color": "radical", "resultado": None},
    "Santiago del Estero": {"nombre": "Elías Suárez", "partido": "Frente Cívico por Santiago (partido provincial)", "color": "otro",
                     "resultado": [("Suárez (Frente Cívico)", 69.8), ("Despierta Santiago", 12.3), ("La Libertad Avanza", 12.0)]},
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur": {"nombre": "Gustavo Melella", "partido": "Unión por la Patria (PJ)", "color": "peronismo", "resultado": None},
    "Tucumán": {"nombre": "Osvaldo Jaldo", "partido": "Unión por la Patria (PJ)", "color": "peronismo", "resultado": None},
}

def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    return texto.lower().strip()

_PROVINCIAS_NORMALIZADAS = {_normalizar(k): k for k in PROVINCIA_MEDIOS}

def buscar_medios_provincia(provincia: str):
    if not provincia:
        return []
    norm = _normalizar(provincia)
    if norm in _PROVINCIAS_NORMALIZADAS:
        return PROVINCIA_MEDIOS[_PROVINCIAS_NORMALIZADAS[norm]]
    for norm_key, original in _PROVINCIAS_NORMALIZADAS.items():
        if norm_key in norm or norm in norm_key:
            return PROVINCIA_MEDIOS[original]
    return []

def buscar_gobernador(provincia: str):
    if not provincia:
        return None
    norm = _normalizar(provincia)
    for key, info in GOBERNADORES.items():
        nk = _normalizar(key)
        if nk == norm or nk in norm or norm in nk:
            return key, info
    return None

def color_provincia_mapa(nombre_geojson: str) -> str:
    resultado = buscar_gobernador(nombre_geojson or "")
    if resultado:
        _, info = resultado
        return COLOR_PARTIDO.get(info["color"], "#cccccc")
    return "#cccccc"

PALABRAS_RUIDO = [
    "contacto", "quienes somos", "quiénes somos", "publicidad", "politica de privacidad",
    "política de privacidad", "terminos y condiciones", "términos y condiciones", "aviso legal",
    "mapa del sitio", "suscribite", "suscripcion", "suscripción", "newsletter",
    "trabaja con nosotros", "staff", "nosotros", "defensor del lector", "codigo de etica",
    "código de ética", "publicanos", "anunciar"
]

def es_ruido(titulo: str, link: str) -> bool:
    t = titulo.lower()
    l = link.lower()
    if len(titulo.strip()) < 12:
        return True
    return any(p in t or p in l for p in PALABRAS_RUIDO)

@st.cache_data(ttl=600)
def obtener_noticias_provincia(provincia: str):
    medios = buscar_medios_provincia(provincia)
    noticias = []
    for nombre_medio, dominio in medios:
        try:
            url = f"https://news.google.com/rss/search?q=site:{dominio}&hl=es-419&gl=AR&ceid=AR:es-419"
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                titulo = entry.title
                if " - " in titulo:
                    titulo = titulo.rsplit(" - ", 1)[0]
                if es_ruido(titulo, entry.link):
                    continue
                try:
                    f = datetime(*entry.published_parsed[:6])
                except Exception:
                    f = datetime.now()
                noticias.append({"titulo": titulo, "link": entry.link, "medio": nombre_medio, "fecha": f})
                if len([n for n in noticias if n["medio"] == nombre_medio]) >= 6:
                    break
        except Exception:
            continue
    noticias.sort(key=lambda x: x["fecha"], reverse=True)
    return noticias

# ========== FUNCIONES DE COTIZACIONES (uso general) ==========
@st.cache_data(ttl=300)
def obtener_precio_yahoo(symbol: str):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NoticiasApp/1.0)"}
        r = requests.get(url, headers=headers, params={"interval": "1d", "range": "5d"}, timeout=6)
        data = r.json()
        resultado = data["chart"]["result"][0]
        meta = resultado["meta"]
        precio = meta.get("regularMarketPrice")
        previo = meta.get("previousClose") or meta.get("chartPreviousClose")
        if precio is None or previo is None:
            cierres = [c for c in resultado["indicators"]["quote"][0]["close"] if c is not None]
            if len(cierres) >= 2:
                precio, previo = cierres[-1], cierres[-2]
        if precio is None or previo is None:
            return None
        cambio = ((precio / previo) - 1) * 100
        return precio, cambio
    except Exception:
        return None

@st.cache_data(ttl=300)
def obtener_dolar(casa: str):
    try:
        r = requests.get(f"https://dolarapi.com/v1/dolares/{casa}", timeout=6)
        d = r.json()
        if d.get("venta") is None:
            return None
        return {"compra": d.get("compra"), "venta": d.get("venta")}
    except Exception:
        return None

@st.cache_data(ttl=300)
def obtener_riesgo_pais():
    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais/ultimo", timeout=6)
        d = r.json()
        return d.get("valor")
    except Exception:
        return None

# ========== INDICADORES ECONÓMICOS: TICKER ANIMADO (arriba del mapa) ==========
st.subheader("Panorama económico")

def _item_ticker(nombre: str, valor: str, en_dolares: bool) -> str:
    sufijo = ' <span style="font-size:10px;font-weight:600;color:#9aa5b1;">USD</span>' if en_dolares else ""
    return (
        f'<span style="display:inline-flex;align-items:baseline;gap:7px;margin:0 26px;white-space:nowrap;'
        f'font-family:Inter,sans-serif;">'
        f'<span style="font-size:11px;font-weight:700;letter-spacing:.5px;color:#8fa6bd;">{nombre.upper()}</span>'
        f'<span style="font-size:16px;font-weight:800;color:#ffffff;">{valor}</span>{sufijo}'
        f'<span style="color:#3a5a78;margin-left:19px;">•</span></span>'
    )

_items_ticker = []

blue = obtener_dolar("blue")
_items_ticker.append(_item_ticker("Dólar Blue", f'${blue["venta"]:.0f}' if blue else "sin datos", False))

oficial = obtener_dolar("oficial")
_items_ticker.append(_item_ticker("Dólar Oficial", f'${oficial["venta"]:.0f}' if oficial else "sin datos", False))

riesgo = obtener_riesgo_pais()
_items_ticker.append(_item_ticker("Riesgo País", f'{riesgo:,.0f} pb' if riesgo is not None else "sin datos", False))

COMMODITIES = [
    ("Petróleo WTI", "CL=F"),
    ("Petróleo Brent", "BZ=F"),
    ("Gas Natural", "NG=F"),
    ("Oro", "GC=F"),
    ("Plata", "SI=F"),
    ("Litio (ETF LIT)", "LIT"),
    ("Soja", "ZS=F"),
    ("Maíz", "ZC=F"),
    ("Trigo", "ZW=F"),
]

for nombre, symbol in COMMODITIES:
    resultado = obtener_precio_yahoo(symbol)
    if resultado:
        precio, _cambio = resultado
        _items_ticker.append(_item_ticker(nombre, f'{precio:,.2f}', True))
    else:
        _items_ticker.append(_item_ticker(nombre, "sin datos", False))

_pista = "".join(_items_ticker)
st.markdown(f"""
<div style="background:linear-gradient(120deg,#0B2E4F,#123A5E);border-radius:10px;
            padding:14px 0;overflow:hidden;margin-bottom:6px;box-shadow:0 4px 12px rgba(11,46,79,.25);">
    <div style="display:inline-block;white-space:nowrap;animation:ticker-economico 42s linear infinite;">
        {_pista}{_pista}
    </div>
</div>
<style>
@keyframes ticker-economico {{
    0% {{ transform: translateX(0); }}
    100% {{ transform: translateX(-50%); }}
}}
</style>
""", unsafe_allow_html=True)

st.caption("Fuentes: DolarAPI, ArgentinaDatos y Yahoo Finance. El litio no tiene un futuro cotizado de acceso público masivo, por eso se aproxima con el ETF LIT (Global X Lithium & Battery Tech).")

st.markdown("---")

# ========== HERRAMIENTAS: COTIZADOR Y CALCULADORA ==========
st.subheader("Herramientas")
col_cotizador, col_calculadora = st.columns(2)

with col_cotizador:
    st.markdown("**Cotizador de dólar**")
    tipo_dolar = st.radio("Cotización", ["Blue", "Oficial"], horizontal=True, key="tipo_dolar")
    valor_dolar = blue["venta"] if (tipo_dolar == "Blue" and blue) else (oficial["venta"] if oficial else None)
    if valor_dolar:
        col_monto, col_direccion = st.columns([1.3, 1])
        with col_direccion:
            direccion = st.selectbox("Convertir", ["ARS → USD", "USD → ARS"], key="direccion_dolar")
        with col_monto:
            monto = st.number_input("Monto", min_value=0.0, value=1000.0, step=100.0, key="monto_dolar")
        if direccion == "ARS → USD":
            resultado_conv = monto / valor_dolar
            st.success(f"${monto:,.0f} ARS = USD {resultado_conv:,.2f} (dólar {tipo_dolar.lower()} a ${valor_dolar:,.0f})")
        else:
            resultado_conv = monto * valor_dolar
            st.success(f"USD {monto:,.0f} = ${resultado_conv:,.2f} ARS (dólar {tipo_dolar.lower()} a ${valor_dolar:,.0f})")
    else:
        st.info("No se pudo obtener la cotización en este momento.")

with col_calculadora:
    st.markdown("**Calculadora de sueldo y aguinaldo**")
    sueldo_bruto = st.number_input("Mejor sueldo bruto del semestre ($)", min_value=0.0, value=1000000.0, step=10000.0, key="sueldo_bruto")
    aguinaldo = sueldo_bruto / 2
    descuentos = sueldo_bruto * 0.17  # jubilación 11% + obra social 3% + PAMI 3%, aprox.
    sueldo_neto_aprox = sueldo_bruto - descuentos
    st.write(f"**Aguinaldo (SAC) estimado:** ${aguinaldo:,.0f}")
    st.write(f"**Sueldo neto aproximado:** ${sueldo_neto_aprox:,.0f}")
    st.caption("Estimación con descuentos típicos en relación de dependencia (jubilación 11% + obra social 3% + PAMI 3% ≈ 17%). Puede variar según convenio, sindicato y otros descuentos.")

st.markdown("---")

# ========== MAPA + BOLSA ==========
col_mapa, col_bolsa = st.columns([1.45, 1])

with col_mapa:
    st.subheader("Provincias")
    st.caption("Rojo = peronismo · Rojo oscuro = radicalismo (UCR) · Amarillo = PRO · Violeta = La Libertad Avanza · Gris = otros partidos")

    @st.cache_data
    def cargar_provincias():
        try:
            r = requests.get("https://apis.datos.gob.ar/georef/api/provincias.geojson", timeout=8)
            return r.json()
        except:
            return None

    geo = cargar_provincias()
    m = folium.Map(location=[-38.4, -63.6], zoom_start=3.9, tiles="CartoDB positron")
    if geo:
        folium.GeoJson(
            geo,
            style_function=lambda x: {
                "fillColor": color_provincia_mapa(x["properties"].get("nombre", "")),
                "color": "#333", "weight": 1, "fillOpacity": 0.62
            },
            highlight_function=lambda x: {"fillColor": "#111", "weight": 2.5, "fillOpacity": 0.75},
            tooltip=folium.GeoJsonTooltip(fields=["nombre"], aliases=["Provincia:"])
        ).add_to(m)
    map_data = st_folium(m, height=310, key="mapa", use_container_width=True)

    provincia_seleccionada = None
    if map_data and map_data.get("last_object_clicked_tooltip"):
        raw = str(map_data["last_object_clicked_tooltip"])
        provincia_seleccionada = re.sub(r'(?i)^Provincia:\s*', '', raw).strip()

    if provincia_seleccionada:
        if st.session_state.get("ultima_provincia") != provincia_seleccionada:
            st.session_state.ultima_provincia = provincia_seleccionada
            st.session_state.ocultar_provincia = False

    # Presidente al pie del mapa
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-top:8px;padding:8px 10px;
                background:white;border:1px solid #e5e2db;border-radius:6px;">
        {sol_de_mayo_svg(28)}
        <div>
            <div style="font-size:10px;color:#888;letter-spacing:.5px;">PRESIDENTE DE LA NACIÓN</div>
            <div style="font-size:14px;font-weight:700;color:#111;">Javier Milei <span style="font-weight:400;color:#666;">· La Libertad Avanza</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Ficha política de la provincia seleccionada
    if provincia_seleccionada and not st.session_state.get("ocultar_provincia", False):
        resultado_gob = buscar_gobernador(provincia_seleccionada)
        if resultado_gob:
            _, info = resultado_gob
            color = COLOR_PARTIDO.get(info["color"], "#888")
            ficha = f"""
            <div style="background:white;border:1px solid #e5e2db;border-radius:8px;padding:12px 14px;margin-top:10px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <span style="width:12px;height:12px;border-radius:50%;background:{color};display:inline-block;"></span>
                    <b style="font-size:15px;color:#111;">{info['nombre']}</b>
                </div>
                <div style="font-size:12px;color:#555;margin-bottom:8px;">Gobernador/a de {prov...
