import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import requests
import re
import unicodedata
import hashlib
import json

st.set_page_config(
    page_title="Noticias de Argentina",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# ========== BANNER ==========
@st.cache_data(ttl=300)
def obtener_titulares_infobae():
    try:
        feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
        return [e.title for e in feed.entries[:7]]
    except:
        return ["Cargando titulares..."]

texto_banner = "  •  ".join(obtener_titulares_infobae())
st.markdown(f"""
<div style="background:#111; color:#f5f0e6; padding:9px 0; font-size:13px; overflow:hidden; white-space:nowrap;">
    <div style="display:inline-block; padding-left:100%; animation: marquee 42s linear infinite;">
        INFOBAE HOY · {texto_banner}
    </div>
</div>
<style>@keyframes marquee {{0%{{transform:translateX(0)}}100%{{transform:translateX(-100%)}}}}</style>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== FECHAS ==========
c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    fecha_desde = st.date_input("Desde", value=datetime.now().date() - timedelta(days=2))
with c2:
    fecha_hasta = st.date_input("Hasta", value=datetime.now().date())
with c3:
    if st.button("Actualizar", use_container_width=True):
        st.rerun()

# ========== SIDEBAR ==========
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

def _chip_indicador(nombre, valor_html, sub=None):
    sub_html = f'<div style="font-size:10px;color:#888;margin-top:1px;">{sub}</div>' if sub else ""
    return f"""
    <div style="background:white;border:1px solid #e5e2db;border-radius:6px;padding:8px 14px;min-width:150px;flex:1;">
        <div style="font-size:10px;color:#666;font-weight:700;letter-spacing:.4px;">{nombre}</div>
        <div style="font-size:17px;font-weight:700;color:#111;">{valor_html}</div>
        {sub_html}
    </div>"""

# ========== INDICADORES ECONÓMICOS (arriba del mapa) ==========
st.subheader("Panorama económico")
st.caption("Dólar, riesgo país, energía, minería y agro")

_chips = []

blue = obtener_dolar("blue")
if blue:
    sub = f'compra ${blue["compra"]:.0f}' if blue.get("compra") else None
    _chips.append(_chip_indicador("DÓLAR BLUE", f'${blue["venta"]:.0f}', sub))
else:
    _chips.append(_chip_indicador("DÓLAR BLUE", "sin datos"))

oficial = obtener_dolar("oficial")
if oficial:
    sub = f'compra ${oficial["compra"]:.0f}' if oficial.get("compra") else None
    _chips.append(_chip_indicador("DÓLAR OFICIAL", f'${oficial["venta"]:.0f}', sub))
else:
    _chips.append(_chip_indicador("DÓLAR OFICIAL", "sin datos"))

riesgo = obtener_riesgo_pais()
if riesgo is not None:
    _chips.append(_chip_indicador("RIESGO PAÍS", f'{riesgo:,.0f} pb'))
else:
    _chips.append(_chip_indicador("RIESGO PAÍS", "sin datos"))

COMMODITIES = [
    ("PETRÓLEO WTI", "CL=F", "u$s/barril"),
    ("PETRÓLEO BRENT", "BZ=F", "u$s/barril"),
    ("ORO", "GC=F", "u$s/oz"),
    ("PLATA", "SI=F", "u$s/oz"),
    ("LITIO (ETF LIT)", "LIT", "proxy, u$s"),
    ("SOJA", "ZS=F", "u$s/bushel"),
    ("MAÍZ", "ZC=F", "u$s/bushel"),
    ("TRIGO", "ZW=F", "u$s/bushel"),
]

for nombre, symbol, unidad in COMMODITIES:
    resultado = obtener_precio_yahoo(symbol)
    if resultado:
        precio, cambio = resultado
        color = "#14804A" if cambio >= 0 else "#C0392B"
        sub = f'<span style="color:{color};font-weight:700;">{cambio:+.2f}%</span> · {unidad}'
        _chips.append(_chip_indicador(nombre, f'{precio:,.2f}', sub))
    else:
        _chips.append(_chip_indicador(nombre, "sin datos"))

st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:4px;">{"".join(_chips)}</div>', unsafe_allow_html=True)
st.caption("Fuentes: DolarAPI, ArgentinaDatos y Yahoo Finance. El litio no tiene un futuro cotizado de acceso público masivo, por eso se aproxima con el ETF LIT (Global X Lithium & Battery Tech).")

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

# ========== ÚLTIMAS LEYES APROBADAS ==========
LEYES_APROBADAS = [
    ("Ley de Presupuesto 2026", "2025-12-18"),
    ("Ley de Inocencia Fiscal", "2025-12-10"),
    ("Prórroga del Consenso Fiscal", "2025-11-27"),
    ("Ley de Boleta Única Papel (reglamentación)", "2025-11-05"),
    ("Modificación del Régimen de Alquileres", "2025-10-22"),
    ("Ley de Emergencia en Discapacidad (financiamiento)", "2025-09-30"),
    ("Actualización del Régimen de Zonas Frías", "2025-09-11"),
    ("Ley de Financiamiento Universitario", "2025-08-27"),
    ("Modificaciones al Código Aduanero", "2025-08-14"),
    ("Ley de Restauración de la Sostenibilidad de la Deuda Pública (ampliación)", "2025-07-30"),
]

st.subheader("Últimas leyes aprobadas")
st.caption("Las 10 sanciones más recientes del Congreso. Nómina de referencia, editable a medida que se sancionan nuevas leyes; para el detalle oficial consultá hcdn.gob.ar o senado.gob.ar.")
filas_leyes = ""
for i, (nombre_ley, fecha_ley) in enumerate(LEYES_APROBADAS[:10], start=1):
    filas_leyes += f"""
    <div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #eee;">
        <span style="font-family:'Playfair Display',serif;font-weight:700;color:#B8860B;font-size:14px;min-width:20px;">{i:02d}</span>
        <span style="font-size:13px;color:#111;flex:1;">{nombre_ley}</span>
        <span style="font-size:11px;color:#888;">{fecha_ley}</span>
    </div>"""
st.markdown(f'<div style="background:white;border:1px solid #e5e2db;border-radius:6px;padding:8px 16px;margin-bottom:14px;">{filas_leyes}</div>', unsafe_allow_html=True)

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
filas_term = ""
for nombre, count in menciones:
    pct = (count / max_menciones * 100) if max_menciones else 0
    filas_term += f"""
    <div style="margin-bottom:8px;">
        <div style="display:flex;justify-content:space-between;font-size:12px;color:#333;margin-bottom:3px;">
            <span><b>{nombre}</b></span><span>{count} menciones</span>
        </div>
        <div style="background:#eee;border-radius:4px;height:10px;overflow:hidden;">
            <div style="width:{pct:.1f}%;background:linear-gradient(90deg,#B8860B,#8B0000);height:100%;"></div>
        </div>
    </div>"""
st.markdown(f'<div style="background:white;border:1px solid #e5e2db;border-radius:6px;padding:14px 16px;">{filas_term}</div>', unsafe_allow_html=True)

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
        if feed.entries:
            e = feed.entries[0]
            return {"titulo": e.title, "link": e.link, "imagen": extraer_imagen(e)}
    except:
        return None
    return None

@st.cache_data(ttl=180)
def obtener_tapa_infobae():
    """Intenta traer la noticia principal (la número 1) de la tapa de Infobae en este momento."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NoticiasApp/1.0)"}
        r = requests.get("https://www.infobae.com/", headers=headers, timeout=8)
        html = r.text
        link = None

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
                        if url_it and "infobae.com" in url_it and "/arc/outboundfeeds" not in url_it:
                            link = url_it
                            break
                if link:
                    break
            if link:
                break

        # Estrategia 2 (respaldo): primer link de nota que aparece en el HTML de portada
        if not link:
            m = re.search(r'href="(https://www\.infobae\.com/[a-z0-9\-]+/\d{4}/\d{2}/\d{2}/[a-z0-9\-]+/)"', html)
            if m:
                link = m.group(1)

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
        <a href="{n_infobae['link']}" target="_blank">Leer en Infobae →</a>
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
            <a href="{n['link']}" target="_blank">Leer nota completa →</a>
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

# ========== ZÓCALOS PUBLICITARIOS ==========
st.caption("Espacios publicitarios")


def _zocalo_publicidad(alto="90px"):
    return f"""
    <div style="background:repeating-linear-gradient(45deg,#f0ede6,#f0ede6 10px,#e8e4da 10px,#e8e4da 20px);
                border:1.5px dashed #c9c2b3;border-radius:6px;height:{alto};
                display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
        <span style="color:#9a9282;font-size:13px;font-weight:600;letter-spacing:.5px;">PUBLICITE AQUÍ</span>
    </div>"""
    # Reemplazar este bloque por el snippet de Google Ad Manager / AdSense correspondiente a cada zócalo.


cols_ads_1 = st.columns(3)
for c in cols_ads_1:
    with c:
        st.markdown(_zocalo_publicidad(), unsafe_allow_html=True)

cols_ads_2 = st.columns(3)
for c in cols_ads_2:
    with c:
        st.markdown(_zocalo_publicidad(), unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center;padding:25px 0 10px;color:#888;font-size:12px;border-top:1px solid #ddd;margin-top:30px;">
    Noticias de Argentina
</div>
""", unsafe_allow_html=True)
