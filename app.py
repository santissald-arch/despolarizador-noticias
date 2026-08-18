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
                <div style="font-size:12px;color:#555;margin-bottom:8px;">Gobernador/a de {provincia_seleccionada} · {info['partido']}</div>
            """
            if info["resultado"]:
                max_pct = max(p for _, p in info["resultado"])
                filas = ""
                for i, (nombre_c, pct) in enumerate(info["resultado"]):
                    barra_color = color if i == 0 else "#c7c7c7"
                    filas += f"""
                    <div style="margin-bottom:5px;">
                        <div style="font-size:11px;color:#333;display:flex;justify-content:space-between;">
                            <span>{nombre_c}</span><span><b>{pct:.1f}%</b></span>
                        </div>
                        <div style="background:#eee;border-radius:4px;height:8px;overflow:hidden;">
                            <div style="width:{pct/max_pct*100:.1f}%;background:{barra_color};height:100%;"></div>
                        </div>
                    </div>"""
                ficha += f'<div style="font-size:11px;color:#888;margin-bottom:4px;">Cómo ganó la gobernación:</div>{filas}'
            ficha += "</div>"
            st.markdown(ficha, unsafe_allow_html=True)

with col_bolsa:
    st.subheader("Mercados")
    st.caption("EE.UU. · Argentina")

    TICKERS = [
        ("S&P 500", "^GSPC"), ("Dow Jones", "^DJI"), ("Nasdaq", "^IXIC"),
        ("Merval", "^MERV"), ("YPF", "YPF"), ("Galicia", "GGAL"),
    ]

    hubo_error = False
    for nombre, symbol in TICKERS:
        resultado = obtener_precio_yahoo(symbol)
        if resultado:
            precio, cambio = resultado
            color = "#14804A" if cambio >= 0 else "#C0392B"
            st.markdown(f"""
            <div class="mercado-box">
                <span style="font-weight:600;font-size:14px;color:#1a1a1a;">{nombre}</span>
                <span>
                    <b style="font-size:14px;color:#1a1a1a;">{precio:,.2f}</b>
                    <span style="color:{color};font-size:12px;margin-left:6px;font-weight:600;">({cambio:+.2f}%)</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            hubo_error = True
            st.markdown(f"""
            <div class="mercado-box">
                <span style="font-weight:600;font-size:14px;color:#1a1a1a;">{nombre}</span>
                <span style="color:#888;font-size:12px;">sin datos</span>
            </div>
            """, unsafe_allow_html=True)

    if hubo_error:
        st.caption("Algunos valores no se pudieron actualizar en este momento.")

st.markdown("---")

# ========== CONGRESO ==========
def barra_bancas(datos, total):
    segmentos = "".join([
        f'<div style="width:{count/total*100:.2f}%;background:{color};height:100%;" title="{nombre}: {count}"></div>'
        for nombre, count, color in datos
    ])
    leyenda = "".join([
        f'<div style="display:flex;align-items:center;gap:6px;margin:3px 12px 3px 0;font-size:12px;color:#333;">'
        f'<span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;"></span>'
        f'{nombre} ({count})</div>'
        for nombre, count, color in datos
    ])
    return f"""
    <div style="display:flex;height:22px;border-radius:6px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.15);margin-bottom:8px;">{segmentos}</div>
    <div style="display:flex;flex-wrap:wrap;">{leyenda}</div>
    """

DIPUTADOS = [
    ("La Libertad Avanza", 95, COLOR_PARTIDO["lla"]),
    ("Unión por la Patria", 93, COLOR_PARTIDO["peronismo"]),
    ("Provincias Unidas", 18, "#16A085"),
    ("PRO", 12, COLOR_PARTIDO["pro"]),
    ("UCR", 6, "#3498DB"),
    ("Otros bloques", 257 - 95 - 93 - 18 - 12 - 6, "#95A5A6"),
]
SENADO = [
    ("La Libertad Avanza", 20, COLOR_PARTIDO["lla"]),
    ("Fuerza Patria (peronismo)", 28, COLOR_PARTIDO["peronismo"]),
    ("Provincias Unidas", 3, "#16A085"),
    ("Partidos provinciales", 6, "#8C97A6"),
    ("Otros", 15, "#95A5A6"),
]

st.subheader("El Congreso, banca por banca")
st.caption("Composición vigente desde el recambio legislativo de diciembre de 2025")
col_dip, col_sen = st.columns(2)
with col_dip:
    st.markdown("**Cámara de Diputados** (257 bancas)")
    st.markdown(barra_bancas(DIPUTADOS, 257), unsafe_allow_html=True)
with col_sen:
    st.markdown("**Senado** (72 bancas)")
    st.markdown(barra_bancas(SENADO, 72), unsafe_allow_html=True)

st.markdown(f"""
<div style="background:white;border:1px solid #e5e2db;border-left:4px solid #B8860B;border-radius:6px;
            padding:12px 16px;margin:14px 0;display:flex;gap:16px;flex-wrap:wrap;">
    <div style="flex:1;min-width:220px;">
        <div style="font-size:12px;color:#14804A;font-weight:700;margin-bottom:4px;">✔ SE APROBARON</div>
        <div style="font-size:13px;color:#333;">Presupuesto 2026 · Ley de Inocencia Fiscal</div>
    </div>
    <div style="flex:1;min-width:220px;">
        <div style="font-size:12px;color:#B8860B;font-weight:700;margin-bottom:4px;">🕐 EN DEBATE</div>
        <div style="font-size:13px;color:#333;">Reforma laboral · Reforma tributaria · Reforma previsional · Acuerdo Mercosur–Unión Europea</div>
    </div>
</div>
<div style="font-size:11px;color:#888;margin-top:-8px;margin-bottom:10px;">
    Resumen orientativo: el estado de cada proyecto cambia con frecuencia. Para el detalle en tiempo real, consultá hcdn.gob.ar o senado.gob.ar.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== TERMÓMETRO POLÍTICO EN REDES / MEDIOS ==========
POLITICOS_TERMOMETRO = [
    "Javier Milei", "Cristina Kirchner", "Axel Kicillof", "Patricia Bullrich",
    "Mauricio Macri", "Martín Llaryora", "Máximo Kirchner", "Diego Santilli",
]

@st.cache_data(ttl=1800)
def obtener_menciones_politicos():
    resultados = []
    for nombre in POLITICOS_TERMOMETRO:
        try:
            consulta = nombre.replace(" ", "+")
            url = f"https://news.google.com/rss/search?q=%22{consulta}%22+when:1d&hl=es-419&gl=AR&ceid=AR:es-419"
            feed = feedparser.parse(url)
            resultados.append((nombre, len(feed.entries)))
        except Exception:
            resultados.append((nombre, 0))
    resultados.sort(key=lambda x: x[1], reverse=True)
    return resultados

st.subheader("Termómetro político")
st.caption("Este entorno no tiene acceso a APIs de redes sociales (X, Instagram, TikTok), así que el ranking se arma contando menciones en titulares de noticias de las últimas 24 horas, como aproximación de quién está más presente en la conversación pública.")

menciones = obtener_menciones_politicos()
max_menciones = max([m for _, m in menciones] or [1]) or 1
min_menciones = min([m for _, m in menciones] or [0])
rango = max(1, max_menciones - min_menciones)
nombres_html = ""
for nombre, count in menciones:
    ratio = (count - min_menciones) / rango
    tam = 16 + ratio * 34       # 16px a 50px
    peso = 500 + int(ratio * 400)  # 500 a 900
    opacidad = 0.5 + ratio * 0.5
    nombres_html += (
        f'<span title="{count} menciones" '
        f'style="font-family:\'Playfair Display\',serif;font-size:{tam:.0f}px;'
        f'font-weight:{peso};color:#8B0000;opacity:{opacidad:.2f};'
        f'margin:6px 16px;display:inline-block;line-height:1.3;">{nombre}</span>'
    )
st.markdown(
    f'<div style="background:white;border:1px solid #e5e2db;border-radius:6px;'
    f'padding:26px 20px;text-align:center;">{nombres_html}</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# ========== SERVICIOS: HORÓSCOPO, QUINIELA Y TRÁNSITO ==========
_SIGNOS = [
    ("Aries", "♈"), ("Tauro", "♉"), ("Géminis", "♊"), ("Cáncer", "♋"),
    ("Leo", "♌"), ("Virgo", "♍"), ("Libra", "♎"), ("Escorpio", "♏"),
    ("Sagitario", "♐"), ("Capricornio", "♑"), ("Acuario", "♒"), ("Piscis", "♓"),
]
_MENSAJES_HOROSCOPO = [
    "Buen momento para tomar decisiones que veías postergando. La energía está de tu lado.",
    "Cuidá los vínculos cercanos: una charla pendiente puede destrabar una tensión.",
    "El trabajo pide foco. Ordená prioridades antes de sumar cosas nuevas.",
    "Un imprevisto económico te obliga a replantear gastos. Nada grave si lo mirás a tiempo.",
    "La energía está alta: aprovechá para avanzar en lo que venías dejando para después.",
    "Momento de escuchar más que hablar. Las respuestas pueden venir de donde menos lo esperás.",
    "Se abre una oportunidad laboral o de estudio. Prestá atención a los detalles.",
    "La salud pide un poco de descanso. No te sobre-exijas hoy.",
    "Buen día para lo social: encuentros y conversaciones que suman.",
    "Evitá discusiones por temas de dinero compartido. Mejor hablarlo con calma.",
    "Se favorece todo lo creativo. Si tenés una idea dando vueltas, es momento de anotarla.",
    "La intuición está afilada: confiá en tu primera impresión sobre una decisión pendiente.",
]

def _horoscopo_del_dia(indice_signo: int) -> str:
    dia_del_anio = datetime.now().timetuple().tm_yday
    return _MENSAJES_HOROSCOPO[(dia_del_anio + indice_signo) % len(_MENSAJES_HOROSCOPO)]

@st.cache_data(ttl=1800)
def obtener_noticias_transito():
    try:
        url = "https://news.google.com/rss/search?q=cortes+de+ruta+OR+tr%C3%A1nsito+Buenos+Aires&hl=es-419&gl=AR&ceid=AR:es-419"
        feed = feedparser.parse(url)
        notas = []
        for entry in feed.entries[:4]:
            titulo = entry.title
            if " - " in titulo:
                titulo = titulo.rsplit(" - ", 1)[0]
            notas.append({"titulo": titulo, "link": entry.link})
        return notas
    except Exception:
        return []

col_horoscopo, col_quiniela, col_transito = st.columns(3)

with col_horoscopo:
    st.subheader("Horóscopo del día")
    signo_elegido = st.selectbox("Tu signo", [s[0] for s in _SIGNOS], key="signo_horoscopo")
    idx_signo = [s[0] for s in _SIGNOS].index(signo_elegido)
    simbolo = _SIGNOS[idx_signo][1]
    st.markdown(f"""
    <div class="noticia-card">
        <div style="font-size:32px;text-align:center;">{simbolo}</div>
        <div style="font-size:13px;color:#333;text-align:center;margin-top:6px;line-height:1.4;">
            {_horoscopo_del_dia(idx_signo)}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_quiniela:
    st.subheader("Quiniela y sorteos")
    st.markdown("""
    <div class="noticia-card">
        <div style="font-size:13px;color:#333;line-height:1.5;">
            Los resultados de Quiniela Nacional, Provincia, Loto y Brinco cambian varias veces al día,
            así que para el número exacto y actualizado te conviene ir a la fuente oficial.
        </div>
        <div style="margin-top:10px;">
            <a href="https://www.loteria.gov.ar" target="_blank">Loteria Nacional →</a><br>
            <a href="https://www.loteriadebuenosaires.gob.ar" target="_blank">Lotería de Buenos Aires →</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_transito:
    st.subheader("Tránsito y rutas")
    noticias_transito = obtener_noticias_transito()
    if noticias_transito:
        for nt in noticias_transito:
            st.markdown(f"""
            <div class="noticia-card" style="padding:10px 12px;margin-bottom:8px;">
                <a href="{nt['link']}" target="_blank" style="font-size:12px;color:#111!important;line-height:1.3;">{nt['titulo']}</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No se encontraron novedades de tránsito en este momento.")

st.markdown("---")

# ========== NOTICIAS DE LA PROVINCIA SELECCIONADA ==========
if provincia_seleccionada and not st.session_state.get("ocultar_provincia", False):
    medios_provincia = buscar_medios_provincia(provincia_seleccionada)
    if medios_provincia:
        col_titulo, col_cerrar = st.columns([5, 1])
        with col_titulo:
            st.subheader(f"Noticias de {provincia_seleccionada}")
            nombres_lista = [m[0] for m in medios_provincia]
            if len(nombres_lista) > 1:
                nombres_fuentes = ", ".join(nombres_lista[:-1]) + " y " + nombres_lista[-1]
            else:
                nombres_fuentes = nombres_lista[0] if nombres_lista else ""
            st.caption(f"Fuentes: {nombres_fuentes}")
        with col_cerrar:
            if st.button("✕ Cerrar", use_container_width=True):
                st.session_state.ocultar_provincia = True
                st.rerun()

        with st.spinner("Buscando noticias locales..."):
            noticias_provincia = obtener_noticias_provincia(provincia_seleccionada)

        if noticias_provincia:
            cols_prov = st.columns(2)
            for i, n in enumerate(noticias_provincia[:10]):
                with cols_prov[i % 2]:
                    st.markdown(f"""
                    <div class="noticia-card">
                        {chip_medio(n['medio'])}
                        <div style="font-family:'Playfair Display',serif;font-size:15px;font-weight:600;
                                    line-height:1.35;margin-top:8px;">
                            <a href="{n['link']}" target="_blank" style="color:#111!important;">{n['titulo']}</a>
                        </div>
                        {boton_whatsapp(n['titulo'], n['link'])}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No se encontraron noticias recientes para esta provincia.")
        st.markdown("---")
    else:
        st.caption(f"Todavía no tenemos diarios cargados para {provincia_seleccionada}.")

# ========== DESTACADOS ==========
st.subheader("Destacados del día")

def extraer_imagen(entry):
    if hasattr(entry, "media_content") and entry.media_content:
        for m in entry.media_content:
            url = m.get("url")
            if url and any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                return url
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    content = ""
    if entry.get("content"):
        content = entry.content[0].get("value", "")
    elif entry.get("summary"):
        content = entry.summary
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
    return match.group(1) if match else None

@st.cache_data(ttl=300)
def obtener_noticia_infobae_rss():
    try:
        feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
        excluidas = ["/mexico/", "/colombia/", "/chile/", "/peru/", "/venezuela/",
                     "/america/", "/estados-unidos/", "/espana/"]
        for e in feed.entries[:15]:
            if not any(seccion in e.link for seccion in excluidas):
                return {"titulo": e.title, "link": e.link, "imagen": extraer_imagen(e)}
    except Exception:
        return None
    return None

@st.cache_data(ttl=180)
def obtener_tapa_infobae():
    """Intenta traer la noticia principal (la número 1) de la sección Argentina de Infobae."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NoticiasApp/1.0)"}
        # Infobae es un medio panregional (tiene ediciones/tapas de México, Colombia, etc.).
        # Para no traer noticias de otros países, se usa específicamente la sección Argentina.
        r = requests.get("https://www.infobae.com/argentina/", headers=headers, timeout=8)
        html = r.text
        link = None

        def _es_nota_argentina(url_it: str) -> bool:
            if "infobae.com" not in url_it or "/arc/outboundfeeds" in url_it:
                return False
            # Excluye explícitamente otras ediciones/países de Infobae
            excluidas = ["/mexico/", "/colombia/", "/chile/", "/peru/", "/venezuela/",
                         "/america/", "/estados-unidos/", "/espana/"]
            if any(seccion in url_it for seccion in excluidas):
                return False
            return True

        # Estrategia 1: bloques JSON-LD tipo ItemList, que reflejan el orden real de la tapa
        for bloque in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
            try:
                data = json.loads(bloque.strip())
            except Exception:
                continue
            candidatos = data if isinstance(data, list) else [data]
            for d in candidatos:
                if isinstance(d, dict) and d.get("@type") == "ItemList":
                    items = d.get("itemListElement", [])
                    items_ordenados = sorted(items, key=lambda x: x.get("position", 999))
                    for it in items_ordenados:
                        url_it = it.get("url") or (it.get("item") or {}).get("url")
                        if url_it and _es_nota_argentina(url_it):
                            link = url_it
                            break
                if link:
                    break
            if link:
                break

        # Estrategia 2 (respaldo): primer link de nota que aparece en el HTML de la sección Argentina
        if not link:
            for m in re.finditer(r'href="(https://www\.infobae\.com/[a-z0-9\-]+/\d{4}/\d{2}/\d{2}/[a-z0-9\-]+/)"', html):
                if _es_nota_argentina(m.group(1)):
                    link = m.group(1)
                    break

        # Estrategia 3 (último respaldo): feed RSS general, filtrando por nota que hable de Argentina
        if not link:
            feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
            for entry in feed.entries[:15]:
                if _es_nota_argentina(entry.link):
                    link = entry.link
                    break

        if not link:
            return None

        r2 = requests.get(link, headers=headers, timeout=8)
        html2 = r2.text
        titulo_m = re.search(r'<meta property="og:title" content="([^"]+)"', html2)
        imagen_m = re.search(r'<meta property="og:image" content="([^"]+)"', html2)
        if not titulo_m:
            return None
        return {
            "titulo": titulo_m.group(1),
            "link": link,
            "imagen": imagen_m.group(1) if imagen_m else None,
        }
    except Exception:
        return None

n_infobae = obtener_tapa_infobae() or obtener_noticia_infobae_rss()

col_a, col_b = st.columns(2)

with col_a:
    if n_infobae:
        st.markdown('<div class="noticia-card">', unsafe_allow_html=True)
        st.markdown(f'{chip_medio("Infobae")} <span style="font-size:11px;color:#8B0000;font-weight:600;margin-left:6px;">TAPA DEL DIARIO</span>', unsafe_allow_html=True)

        if n_infobae.get("imagen"):
            st.image(n_infobae["imagen"], use_container_width=True)
        else:
            st.markdown(get_logo_html("Infobae"), unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-family:'Playfair Display',serif;font-size:20px;font-weight:700;line-height:1.3;margin:12px 0;color:#111;">
            {n_infobae['titulo']}
        </div>
        <a href="{n_infobae['link']}" target="_blank">Leer en Infobae →</a><br>
        {boton_whatsapp(n_infobae['titulo'], n_infobae['link'])}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No se pudo cargar la noticia de Infobae")

with col_b:
    st.markdown(f"""
    <div class="noticia-card">
        {chip_medio("TN")} <span style="font-size:11px;color:#00a0e3;font-weight:600;margin-left:6px;">TRANSMISIÓN EN VIVO</span>
        <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:4px;margin-top:8px;">
            <iframe src="https://www.youtube.com/embed/live_stream?channel=UCj6PcyLvpnIRT_2W_mwa9Aw" 
                    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" 
                    allowfullscreen></iframe>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== COLUMNA DE OPINIÓN POLÍTICA ==========
@st.cache_data(ttl=900)
def obtener_columna_opinion():
    try:
        url = ("https://news.google.com/rss/search?q=(site:infobae.com/opinion+OR+"
               "site:lanacion.com.ar/opinion+OR+site:clarin.com/opinion)&hl=es-419&gl=AR&ceid=AR:es-419")
        feed = feedparser.parse(url)
        notas = []
        for entry in feed.entries[:3]:
            titulo = entry.title
            if " - " in titulo:
                titulo, medio = titulo.rsplit(" - ", 1)
            else:
                medio = "Opinión"
            notas.append({"titulo": titulo, "link": entry.link, "medio": medio})
        return notas
    except Exception:
        return []

st.subheader("Columna de opinión")
st.caption("Análisis y columnas de opinión política de distintos medios")
notas_opinion = obtener_columna_opinion()
if notas_opinion:
    cols_opinion = st.columns(len(notas_opinion))
    for i, nota in enumerate(notas_opinion):
        with cols_opinion[i]:
            st.markdown(f"""
            <div class="noticia-card">
                {chip_medio(nota['medio'])}
                <div style="font-family:'Playfair Display',serif;font-size:15px;font-weight:600;
                            line-height:1.35;margin-top:8px;">
                    <a href="{nota['link']}" target="_blank" style="color:#111!important;">{nota['titulo']}</a>
                </div>
                {boton_whatsapp(nota['titulo'], nota['link'])}
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No se encontraron columnas de opinión en este momento.")

st.markdown("---")

# ========== PARA ENTENDER MEJOR (EXPLICADORES) ==========
@st.cache_data(ttl=1800)
def obtener_explicadores():
    try:
        url = ("https://news.google.com/rss/search?q=%22qu%C3%A9%20significa%22+OR+%22te%20lo%20explicamos%22"
               "+Argentina&hl=es-419&gl=AR&ceid=AR:es-419")
        feed = feedparser.parse(url)
        notas = []
        for entry in feed.entries[:3]:
            titulo = entry.title
            medio = "Medio"
            if " - " in titulo:
                titulo, medio = titulo.rsplit(" - ", 1)
            notas.append({"titulo": titulo, "link": entry.link, "medio": medio})
        return notas
    except Exception:
        return []

st.subheader("Para entender mejor")
st.caption("Notas explicativas sobre los temas del momento")
notas_explicador = obtener_explicadores()
if notas_explicador:
    cols_explicador = st.columns(len(notas_explicador))
    for i, nota in enumerate(notas_explicador):
        with cols_explicador[i]:
            st.markdown(f"""
            <div class="noticia-card">
                {chip_medio(nota['medio'])}
                <div style="font-family:'Playfair Display',serif;font-size:15px;font-weight:600;
                            line-height:1.35;margin-top:8px;">
                    <a href="{nota['link']}" target="_blank" style="color:#111!important;">{nota['titulo']}</a>
                </div>
                {boton_whatsapp(nota['titulo'], nota['link'])}
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No se encontraron notas explicativas en este momento.")

st.markdown("---")

# ========== TABLA DEL TORNEO AFA (2 ZONAS) + NOTICIA DEL TORNEO ==========
def _buscar_zonas_tabla(obj, nombre_actual=None, resultados=None):
    """Recorre el JSON de ESPN y junta TODAS las listas de equipos que encuentra,
    intentando arrastrar el nombre de zona/grupo más cercano (ej. 'Zona A')."""
    if resultados is None:
        resultados = []
    if isinstance(obj, dict):
        entries = obj.get("entries")
        if isinstance(entries, list) and entries and isinstance(entries[0], dict) and "team" in entries[0]:
            nombre_zona = nombre_actual or obj.get("name") or obj.get("displayName") or f"Zona {len(resultados) + 1}"
            firma = tuple(e.get("team", {}).get("displayName") for e in entries)
            if firma not in [r[2] for r in resultados]:
                resultados.append((nombre_zona, entries, firma))
            return resultados
        nombre_aqui = obj.get("name") or obj.get("displayName") or obj.get("abbreviation") or nombre_actual
        for k, v in obj.items():
            if k == "entries":
                continue
            _buscar_zonas_tabla(v, nombre_aqui, resultados)
    elif isinstance(obj, list):
        for item in obj:
            _buscar_zonas_tabla(item, nombre_actual, resultados)
    return resultados

@st.cache_data(ttl=900)
def obtener_zonas_afa():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; NoticiasApp/1.0)"}
    urls = [
        "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/standings",
        "https://site.web.api.espn.com/apis/v2/sports/soccer/arg.1/standings",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code != 200:
                continue
            data = r.json()
            zonas_crudas = _buscar_zonas_tabla(data)
            if not zonas_crudas:
                continue
            zonas = []
            for nombre_zona, entries, _firma in zonas_crudas:
                tabla = []
                for e in entries:
                    team = e.get("team", {})
                    equipo = team.get("displayName") or team.get("name") or "—"
                    escudo = None
                    logos = team.get("logos")
                    if isinstance(logos, list) and logos:
                        escudo = logos[0].get("href")
                    elif team.get("logo"):
                        escudo = team.get("logo")
                    stats = {s.get("name"): s.get("value") for s in e.get("stats", []) if isinstance(s, dict)}
                    tabla.append({
                        "equipo": equipo, "escudo": escudo,
                        "pj": stats.get("gamesPlayed"), "pg": stats.get("wins"),
                        "pe": stats.get("ties"), "pp": stats.get("losses"),
                        "pts": stats.get("points"),
                    })
                if tabla:
                    tabla.sort(key=lambda x: (x["pts"] if x["pts"] is not None else -1), reverse=True)
                    zonas.append((nombre_zona, tabla))
            if zonas:
                return zonas
        except Exception:
            continue
    return None

@st.cache_data(ttl=600)
def obtener_noticia_torneo():
    try:
        url = "https://news.google.com/rss/search?q=Liga+Profesional+Argentina+AFA&hl=es-419&gl=AR&ceid=AR:es-419"
        feed = feedparser.parse(url)
        if not feed.entries:
            return None
        entry = feed.entries[0]
        titulo = entry.title
        medio = "Medio"
        if " - " in titulo:
            titulo, medio = titulo.rsplit(" - ", 1)
        return {"titulo": titulo, "link": entry.link, "medio": medio, "imagen": extraer_imagen(entry)}
    except Exception:
        return None

def _tabla_zona_html(equipos) -> str:
    filas = ""
    for i, eq in enumerate(equipos, start=1):
        if eq.get("escudo"):
            escudo_html = f'<img src="{eq["escudo"]}" style="width:20px;height:20px;object-fit:contain;vertical-align:middle;margin-right:8px;">'
        else:
            escudo_html = '<span style="display:inline-block;width:20px;height:20px;margin-right:8px;"></span>'
        fondo_fila = "#f7f9fb" if i % 2 == 0 else "#ffffff"
        filas += f"""
        <tr style="background:{fondo_fila};border-bottom:1px solid #edf0f3;">
            <td style="padding:7px 6px;color:#8fa6bd;font-weight:700;">{i}</td>
            <td style="padding:7px 6px;text-align:left;color:#111;font-weight:600;">{escudo_html}{eq['equipo']}</td>
            <td style="padding:7px 6px;">{eq['pj'] if eq['pj'] is not None else '-'}</td>
            <td style="padding:7px 6px;">{eq['pg'] if eq['pg'] is not None else '-'}</td>
            <td style="padding:7px 6px;">{eq['pe'] if eq['pe'] is not None else '-'}</td>
            <td style="padding:7px 6px;">{eq['pp'] if eq['pp'] is not None else '-'}</td>
            <td style="padding:7px 6px;font-weight:800;color:#0B2E4F;">{eq['pts'] if eq['pts'] is not None else '-'}</td>
        </tr>"""
    return f"""
    <div style="background:white;border:1px solid #e5e2db;border-radius:0 8px 8px 8px;padding:4px 12px 10px;overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:12.5px;text-align:center;">
    <thead><tr style="border-bottom:2px solid #0B2E4F;color:#0B2E4F;">
        <th style="padding:8px 6px;">#</th><th style="padding:8px 6px;text-align:left;">Equipo</th>
        <th style="padding:8px 6px;">PJ</th><th style="padding:8px 6px;">PG</th>
        <th style="padding:8px 6px;">PE</th><th style="padding:8px 6px;">PP</th>
        <th style="padding:8px 6px;">Pts</th>
    </tr></thead>
    <tbody>{filas}</tbody>
    </table>
    </div>"""

col_tabla, col_noticia_torneo = st.columns([1.6, 1])

with col_tabla:
    st.subheader("Tabla del torneo (AFA)")
    zonas_afa = obtener_zonas_afa()
    if zonas_afa:
        if len(zonas_afa) > 1:
            tabs_zonas = st.tabs([nombre for nombre, _ in zonas_afa])
            for tab, (_nombre, equipos) in zip(tabs_zonas, zonas_afa):
                with tab:
                    st.markdown(_tabla_zona_html(equipos), unsafe_allow_html=True)
        else:
            st.markdown(_tabla_zona_html(zonas_afa[0][1]), unsafe_allow_html=True)
    else:
        st.info("No se pudo cargar la tabla del torneo en este momento. Podés verla directamente en [ESPN](https://www.espn.com.ar/futbol/posiciones/_/liga/arg.1) o en [afa.com.ar](https://www.afa.com.ar).")
    st.caption("Fuente: ESPN. Para la tabla oficial, consultá afa.com.ar.")

with col_noticia_torneo:
    st.subheader("En el torneo")
    noticia_torneo = obtener_noticia_torneo()
    if noticia_torneo:
        st.markdown('<div class="noticia-card">', unsafe_allow_html=True)
        if noticia_torneo.get("imagen"):
            st.image(noticia_torneo["imagen"], use_container_width=True)
        else:
            st.markdown(get_logo_html(noticia_torneo["medio"]), unsafe_allow_html=True)
        st.markdown(f"""
        {chip_medio(noticia_torneo['medio'])}
        <div style="font-family:'Playfair Display',serif;font-size:15px;font-weight:600;
                    line-height:1.35;margin-top:8px;">
            <a href="{noticia_torneo['link']}" target="_blank" style="color:#111!important;">{noticia_torneo['titulo']}</a>
        </div>
        {boton_whatsapp(noticia_torneo['titulo'], noticia_torneo['link'])}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No se encontraron noticias del torneo en este momento.")

st.markdown("---")

# ========== NOTICIAS ==========
st.subheader("Últimas noticias")

TN_FEED = "https://tn.com.ar/arc/outboundfeeds/google-news-feed/?outputType=xml"
INFODEFENSA_FEED = "https://www.infodefensa.com/rss.php"
INFODEFENSA_AR_URL = "https://www.infodefensa.com/america-argentina.php"

feeds_extra = {
    "Política": ["http://cadena3.com/rss/PoliticayEconomia.xml"],
    "Economía": ["http://cadena3.com/rss/PoliticayEconomia.xml"],
    "Defensa / Seguridad": [INFODEFENSA_FEED],
    "Entretenimiento": ["http://cadena3.com/rss/Espectaculos.xml"],
    "Deportes": ["http://cadena3.com/rss/Deportes.xml", "https://www.ole.com.ar/rss/ultimas-noticias/"],
}

PALABRAS_ARGENTINA_DEFENSA = [
    "argentina", "argentino", "argentina/", "faa", "fuerza aerea argentina", "fuerza aérea argentina",
    "ejercito argentino", "ejército argentino", "armada argentina", "milei", "f-16", "f16",
    "ministerio de defensa", "gendarmeria", "gendarmería", "prefectura"
]

def es_defensa_argentina(entry) -> bool:
    texto = (entry.title + " " + entry.link).lower()
    return any(p in texto for p in PALABRAS_ARGENTINA_DEFENSA)

def detectar_categoria_tn(link):
    link = link.lower()
    if "/politica/" in link: return "Política"
    if "/economia/" in link: return "Economía"
    if "/sociedad/" in link: return "Sociedad"
    if "/internacional/" in link: return "Internacional"
    if "/show/" in link or "/espectaculos/" in link: return "Entretenimiento"
    if "/deportes/" in link: return "Deportes"
    if "/policiales/" in link or "/seguridad/" in link: return "Defensa / Seguridad"
    return "Sociedad"

@st.cache_data(ttl=300)
def obtener_noticias(cats, desde, hasta):
    lista = []
    fuentes = [TN_FEED]
    for c in cats:
        fuentes.extend(feeds_extra.get(c, []))

    for url in set(fuentes):
        try:
            feed = feedparser.parse(url)
            medio = "Infodefensa" if "infodefensa" in url else feed.feed.get("title", "Medio")[:40]
            for entry in feed.entries[:30 if "infodefensa" in url else 10]:
                if "infodefensa" in url and not es_defensa_argentina(entry):
                    continue
                try:
                    f = datetime(*entry.published_parsed[:6]).date()
                except:
                    f = datetime.now().date()
                if not (desde <= f <= hasta):
                    continue
                titulo = entry.title
                if "tn.com.ar" in url:
                    cat = detectar_categoria_tn(entry.link)
                    if cat not in cats:
                        continue
                elif "infodefensa" in url:
                    cat = "Defensa / Seguridad"
                else:
                    cat = "Sociedad"
                lista.append({
                    "titulo": titulo, "link": entry.link, "medio": medio, "categoria": cat,
                    "fecha": f, "imagen": extraer_imagen(entry)
                })
                if "infodefensa" in url and len([n for n in lista if n["medio"] == "Infodefensa"]) >= 8:
                    break
        except:
            continue

    # Búsqueda puntual de F-16 para reforzar la sección de Defensa
    if "Defensa / Seguridad" in cats:
        try:
            feed_f16 = feedparser.parse(
                "https://news.google.com/rss/search?q=F-16+Argentina+site:infodefensa.com&hl=es-419&gl=AR&ceid=AR:es-419"
            )
            for entry in feed_f16.entries[:5]:
                try:
                    f = datetime(*entry.published_parsed[:6]).date()
                except Exception:
                    f = datetime.now().date()
                if not (desde <= f <= hasta):
                    continue
                titulo = entry.title.rsplit(" - ", 1)[0] if " - " in entry.title else entry.title
                if any(n["titulo"] == titulo for n in lista):
                    continue
                lista.append({
                    "titulo": titulo, "link": entry.link, "medio": "Infodefensa", "categoria": "Defensa / Seguridad",
                    "fecha": f, "imagen": extraer_imagen(entry)
                })
        except Exception:
            pass

    return lista

if "pagina" not in st.session_state:
    st.session_state.pagina = 0

with st.spinner("Cargando noticias..."):
    noticias = obtener_noticias(categorias_activas, fecha_desde, fecha_hasta)

if "Defensa / Seguridad" in categorias_activas:
    st.caption(f"Las noticias de Infodefensa muestran solo lo referido a Argentina · [Ver más]({INFODEFENSA_AR_URL})")

if noticias:
    noticias = sorted(noticias, key=lambda x: x["fecha"], reverse=True)
    TAMANO = 5
    total = max(1, (len(noticias) - 1) // TAMANO + 1)
    st.session_state.pagina = max(0, min(st.session_state.pagina, total - 1))
    pagina = noticias[st.session_state.pagina * TAMANO : (st.session_state.pagina + 1) * TAMANO]

    if pagina:
        n = pagina[0]
        col1, col2 = st.columns([1.2, 2.8])
        with col1:
            if n.get("imagen"):
                st.image(n["imagen"], use_container_width=True)
            else:
                st.markdown(get_logo_html(n["medio"]), unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="margin-bottom:6px;">{chip_medio(n['medio'])} <span style="font-size:12px;color:#8B0000;font-weight:600;margin-left:6px;">{n['categoria'].upper()}</span></div>
            <div style="font-family:'Playfair Display',serif;font-size:24px;font-weight:700;line-height:1.25;margin-bottom:10px;color:#111;">
                {n['titulo']}
            </div>
            <a href="{n['link']}" target="_blank">Leer nota completa →</a><br>
            {boton_whatsapp(n['titulo'], n['link'])}
            """, unsafe_allow_html=True)

        st.markdown("---")

    resto = pagina[1:]
    if resto:
        cols = st.columns(2)
        for i, n in enumerate(resto):
            with cols[i % 2]:
                with st.container():
                    st.markdown('<div class="noticia-card">', unsafe_allow_html=True)
                    c_img, c_txt = st.columns([1, 2.2])
                    with c_img:
                        if n.get("imagen"):
                            st.image(n["imagen"], use_container_width=True)
                        else:
                            st.markdown(get_logo_html(n["medio"]), unsafe_allow_html=True)
                    with c_txt:
                        st.markdown(f"""
                        <div style="margin-bottom:4px;">{chip_medio(n['medio'])} <span style="font-size:11px;color:#666;margin-left:6px;">{n['fecha']}</span></div>
                        <div style="font-family:'Playfair Display',serif;font-size:15px;font-weight:600;line-height:1.3;">
                            <a href="{n['link']}" target="_blank" style="color:#111!important;">{n['titulo']}</a>
                        </div>
                        {boton_whatsapp(n['titulo'], n['link'])}
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    ca, cb, cc = st.columns([1, 2, 1])
    with ca:
        if st.button("← Anterior", disabled=st.session_state.pagina == 0, use_container_width=True):
            st.session_state.pagina -= 1
            st.rerun()
    with cb:
        st.markdown(f"<div style='text-align:center;padding-top:8px;color:#1a1a1a;'>Página {st.session_state.pagina+1} de {total}</div>", unsafe_allow_html=True)
    with cc:
        if st.button("Siguiente →", disabled=st.session_state.pagina >= total-1, use_container_width=True):
            st.session_state.pagina += 1
            st.rerun()
else:
    st.info("No se encontraron noticias con esos filtros.")

st.markdown("---")

# ========== NEWSLETTER (genera visitas recurrentes) ==========
_ARCHIVO_SUSCRIPTORES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suscriptores.csv")

def guardar_suscriptor(email: str) -> bool:
    try:
        existe = os.path.isfile(_ARCHIVO_SUSCRIPTORES)
        with open(_ARCHIVO_SUSCRIPTORES, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not existe:
                writer.writerow(["email", "fecha"])
            writer.writerow([email, datetime.now().isoformat(timespec="seconds")])
        return True
    except Exception:
        return False

st.markdown(f"""
<div style="background:linear-gradient(120deg,#0B2E4F,#1B4F91);border-radius:12px;padding:26px 30px;
            text-align:center;color:white;margin-bottom:8px;">
    <div style="font-family:'Playfair Display',serif;font-size:22px;font-weight:800;margin-bottom:6px;">
        Recibí el resumen del día en tu mail
    </div>
    <div style="font-size:13px;color:#cfe0f2;">
        Dólar, riesgo país y las noticias más importantes de Argentina, todas las mañanas.
    </div>
</div>
""", unsafe_allow_html=True)

col_news1, col_news2, col_news3 = st.columns([2, 1, 2])
with col_news2:
    email_suscripcion = st.text_input("Tu email", placeholder="tu@email.com", key="email_newsletter", label_visibility="collapsed")
    if st.button("Suscribirme", use_container_width=True, key="btn_newsletter"):
        if email_suscripcion and "@" in email_suscripcion and "." in email_suscripcion.split("@")[-1]:
            if guardar_suscriptor(email_suscripcion):
                st.success("¡Listo! Ya estás suscripto.")
            else:
                st.error("No se pudo guardar la suscripción, intentá de nuevo.")
        else:
            st.warning("Ingresá un email válido.")

st.markdown("---")

# ========== ZÓCALOS PUBLICITARIOS ==========
st.caption("Espacios publicitarios")


def _zocalo_publicidad(alto="220px"):
    return f"""
    <div style="background:repeating-linear-gradient(45deg,#f0ede6,#f0ede6 10px,#e8e4da 10px,#e8e4da 20px);
                border:1.5px dashed #c9c2b3;border-radius:6px;height:{alto};
                display:flex;align-items:center;justify-content:center;margin-bottom:16px;">
        <span style="color:#9a9282;font-size:16px;font-weight:600;letter-spacing:.5px;">PUBLICITE AQUÍ</span>
    </div>"""
    # Reemplazar este bloque por el snippet de Google Ad Manager / AdSense correspondiente a cada zócalo.


for _ in range(5):
    st.markdown(_zocalo_publicidad(), unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center;padding:25px 0 10px;color:#888;font-size:12px;border-top:1px solid #ddd;margin-top:30px;">
    Noticias de Argentina
</div>
""", unsafe_allow_html=True)
