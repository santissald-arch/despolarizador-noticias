import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import requests
import re
import unicodedata
import hashlib

st.set_page_config(
    page_title="Noticias de Argentina",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ESTILO DIARIO CLARO ==========
st.markdown("""
<style>
@import url('https://googleapis.com');

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
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 14px;
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

/* Contenedores para la marquesina e Infobae Fijo */
.header-container {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
}
.marquee-box {
    flex: 2;
    background: #111;
    color: #f5f0e6;
    padding: 12px;
    font-size: 13px;
    overflow: hidden;
    white-space: nowrap;
    border-radius: 6px;
}
.infobae-fijo-box {
    flex: 1;
    background: #e63946;
    color: white !important;
    padding: 12px;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}
.infobae-fijo-box a {
    color: white !important;
    text-decoration: underline;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ========== SOL DE MAYO (logo) ==========
def sol_de_mayo_svg(size=48, color="#EFA400", borde="#B8860B"):
    rayos = ""
    for i in range(16):
        ang = i * (360 / 16)
        rayos += f'<rect x="47" y="1" width="6" height="24" rx="1.5" fill="{color}" transform="rotate({ang} 50 50)"></rect>'
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://w3.org">
        {rayos}
        <circle cx="50" cy="50" r="23" fill="{color}" stroke="{borde}" stroke-width="2"/>
    </svg>'''

st.markdown(f"""
<div style="display:flex;align-items:center;gap:14px;margin-bottom:4px;">
    {sol_de_mayo_svg(46)}
    <h1 style="margin:0;">Noticias de Argentina</h1>
</div>
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

# ========== EXTRACCIÓN DEL FEED DE INFOBAE ==========
@st.cache_data(ttl=300)
def obtener_feed_infobae():
    try:
        return feedparser.parse("https://infobae.com")
    except:
        return None

feed_infobae = obtener_feed_infobae()

# Extraer primera noticia para destacar e hilos secundarios para marquesina móvil
if feed_infobae and feed_infobae.entries:
    primera_noticia = feed_infobae.entries[0]
    titulo_principal = primera_noticia.title
    link_principal = primera_noticia.link
    
    titulares_restantes = [e.title for e in feed_infobae.entries[1:8]]
    texto_marquesina = "  •  ".join(titulares_restantes)
else:
    titulo_principal = "No se pudo cargar la noticia principal de Infobae."
    link_principal = "#"
    texto_marquesina = "Cargando titulares de la marquesina federal..."

# ========== BANNER PREMIUM: MARQUESINA + INFOBAE FIJO ==========
st.markdown(f"""
<div class="header-container">
    <div class="marquee-box">
        <div style="display:inline-block; padding-left:100%; animation: marquee 35s linear infinite;">
            🔴 MÁS TITULARES DE INFOBAE · {texto_marquesina}
        </div>
    </div>
    <div class="infobae-fijo-box">
        <small style="text-transform: uppercase; font-size: 10px; font-weight: 700; opacity: 0.9; display: block; margin-bottom: 2px;">⚡ ALERTA INFOBAE (ÚLTIMO MOMENTO)</small>
        <span style="font-size: 13px; line-height: 1.25; display: block;">
            <a href="{link_principal}" target="_blank">{titulo_principal}</a>
        </span>
    </div>
</div>
<style>@keyframes marquee {{0%{{transform:translateX(0)}}100%{{transform:translateX(-100%)}}}}</style>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== RANGO DE FECHAS ==========
c1, c2, c3 = st.columns(3)
with c1:
    fecha_desde = st.date_input("Desde", value=datetime.now().date() - timedelta(days=2))
with c2:
    fecha_hasta = st.date_input("Hasta", value=datetime.now().date())
with c3:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("Actualizar", use_container_width=True):
        st.rerun()

# ========== BARRA LATERAL (CATEGORÍAS) ==========
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

# ========== DICCIONARIO DE MEDIOS FEDERALES (24 Provincias) ==========
PROVINCIA_MEDIOS = {
    "Buenos Aires": {"coords": [-36.67, -60.50], "medios": [("El Día", "https://eldia.com"), ("Diario Hoy", "https://diariohoy.net")]},
    "CABA": {"coords": [-34.60, -58.38], "medios": [("Clarín", "https://clarin.com"), ("La Nación", "https://lanacion.com.ar")]},
    "Catamarca": {"coords": [-28.46, -65.78], "medios": [("El Ancasti", "https://elancasti.com.ar"), ("El Esquiú", "https://elesquiu.com")]},
    "Chaco": {"coords": [-26.40, -60.80], "medios": [("Diario Norte", "http://diarionorte.com"), ("Chaco Día por Día", "https://chacodiapordia.com")]},
    "Chubut": {"coords": [-43.30, -65.10], "medios": [("El Chubut", "https://elchubut.com.ar"), ("Diario Jornada", "https://diariojornada.com.ar")]},
