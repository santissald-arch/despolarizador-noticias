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
# Fondo claro + texto oscuro forzado en TODOS los elementos (evita que el
# tema oscuro por defecto de Streamlit deje letras claras sobre fondo claro).
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #f7f5f0;
    color: #1a1a1a;
}

.stApp { background-color: #f7f5f0; }

/* Texto oscuro forzado en todo el contenido de la app */
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

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e2db;
}
section[data-testid="stSidebar"] * { color: #1a1a1a !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #111 !important; }

/* Inputs de fecha */
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

.medio-chip {
    display: inline-block;
    color: #ffffff !important;
    padding: 3px 11px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.18);
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

st.title("Noticias de Argentina")

# ========== LOGOS / COLORES DE MEDIOS ==========
LOGOS = {
    "TN": {"color": "#00a0e3", "texto": "TN"},
    "Infobae": {"color": "#e63946", "texto": "INFOBAE"},
    "Cadena 3": {"color": "#1a73e8", "texto": "C3"},
    "La Nación": {"color": "#2b2b2b", "texto": "LA NACIÓN"},
    "Clarín": {"color": "#c8102e", "texto": "CLARÍN"},
    "Olé": {"color": "#ff6600", "texto": "OLÉ"},
    "Infodefensa": {"color": "#2c3e50", "texto": "INFODEFENSA"},
    "default": {"color": "#555", "texto": "MEDIO"}
}

# Paleta de respaldo para diarios provinciales que no están en LOGOS,
# así cada uno tiene un color propio y consistente (nunca negro/plano).
PALETA_MEDIOS = [
    "#0F5C97", "#B5482A", "#2F6F4E", "#7A3B69", "#B08900",
    "#374B8C", "#8C3B3B", "#2E7D6B", "#5B4B8A", "#A2572B", "#1B6E8C", "#6E7A2B"
]

def get_logo_html(medio: str) -> str:
    key = "default"
    for k in LOGOS:
        if k.lower() in medio.lower():
            key = k
            break
    logo = LOGOS[key]
    return f'<div class="logo-badge" style="background:{logo["color"]};">{logo["texto"]}</div>'

def color_para_medio(nombre: str) -> str:
    for k, v in LOGOS.items():
        if k.lower() in nombre.lower():
            return v["color"]
    idx = int(hashlib.md5(nombre.encode("utf-8")).hexdigest(), 16) % len(PALETA_MEDIOS)
    return PALETA_MEDIOS[idx]

def chip_medio(nombre: str) -> str:
    color = color_para_medio(nombre)
    return f'<span class="medio-chip" style="background:{color};">{nombre.upper()}</span>'

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
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur": [("El Sureño", "elsurenio.com.ar"), ("Provincia 23", "provincia23.com.ar")],
    "Tucumán": [("La Gaceta", "lagaceta.com.ar"), ("Contexto Tucumán", "contextotucuman.com")],
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

@st.cache_data(ttl=600)
def obtener_noticias_provincia(provincia: str):
    medios = buscar_medios_provincia(provincia)
    noticias = []
    for nombre_medio, dominio in medios:
        try:
            url = f"https://news.google.com/rss/search?q=site:{dominio}&hl=es-419&gl=AR&ceid=AR:es-419"
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                try:
                    f = datetime(*entry.published_parsed[:6])
                except Exception:
                    f = datetime.now()
                titulo = entry.title
                if " - " in titulo:
                    titulo = titulo.rsplit(" - ", 1)[0]
                noticias.append({
                    "titulo": titulo,
                    "link": entry.link,
                    "medio": nombre_medio,
                    "fecha": f,
                })
        except Exception:
            continue
    noticias.sort(key=lambda x: x["fecha"], reverse=True)
    return noticias

# ========== MAPA + BOLSA ==========
col_mapa, col_bolsa = st.columns([1.45, 1])

with col_mapa:
    st.subheader("Provincias")
    st.caption("Hacé clic en una provincia para ver sus diarios locales")

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
            style_function=lambda x: {"fillColor": "#8B0000", "color": "#333", "weight": 1, "fillOpacity": 0.28},
            highlight_function=lambda x: {"fillColor": "#c0392b", "weight": 2.5, "fillOpacity": 0.55},
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
        if not st.session_state.get("ocultar_provincia", False):
            st.success(f"Filtrando: **{provincia_seleccionada}**")

with col_bolsa:
    st.subheader("Mercados")
    st.caption("EE.UU. · Argentina")

    @st.cache_data(ttl=300)
    def obtener_precio(symbol: str):
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

    TICKERS = [
        ("S&P 500", "^GSPC"),
        ("Dow Jones", "^DJI"),
        ("Nasdaq", "^IXIC"),
        ("Merval", "^MERV"),
        ("YPF", "YPF"),
        ("Galicia", "GGAL"),
    ]

    hubo_error = False
    for nombre, symbol in TICKERS:
        resultado = obtener_precio(symbol)
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

# ========== NOTICIAS DE LA PROVINCIA SELECCIONADA ==========
if provincia_seleccionada and not st.session_state.get("ocultar_provincia", False):
    medios_provincia = buscar_medios_provincia(provincia_seleccionada)
    if medios_provincia:
        col_titulo, col_cerrar = st.columns([5, 1])
        with col_titulo:
            st.subheader(f"Noticias de {provincia_seleccionada}")
            nombres_fuentes = " y ".join([m[0] for m in medios_provincia])
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
def obtener_noticia_infobae():
    try:
        feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
        if feed.entries:
            e = feed.entries[0]
            return {
                "titulo": e.title,
                "link": e.link,
                "imagen": extraer_imagen(e)
            }
    except:
        return None

n_infobae = obtener_noticia_infobae()

col_a, col_b = st.columns(2)

with col_a:
    if n_infobae:
        st.markdown('<div class="noticia-card">', unsafe_allow_html=True)
        st.markdown(f'{chip_medio("Infobae")} <span style="font-size:11px;color:#8B0000;font-weight:600;margin-left:6px;">DESTACADA</span>', unsafe_allow_html=True)

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

feeds_extra = {
    "Política": ["http://cadena3.com/rss/PoliticayEconomia.xml"],
    "Economía": ["http://cadena3.com/rss/PoliticayEconomia.xml"],
    "Defensa / Seguridad": ["https://www.infodefensa.com/rss.php"],
    "Entretenimiento": ["http://cadena3.com/rss/Espectaculos.xml"],
    "Deportes": ["http://cadena3.com/rss/Deportes.xml", "https://www.ole.com.ar/rss/ultimas-noticias/"],
}

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
            medio = feed.feed.get("title", "Medio")[:40]
            for entry in feed.entries[:10]:
                try:
                    f = datetime(*entry.published_parsed[:6]).date()
                except:
                    f = datetime.now().date()
                if not (desde <= f <= hasta):
                    continue
                titulo = entry.title
                cat = detectar_categoria_tn(entry.link) if "tn.com.ar" in url else "Sociedad"
                if "tn.com.ar" in url and cat not in cats:
                    continue
                lista.append({
                    "titulo": titulo,
                    "link": entry.link,
                    "medio": medio,
                    "categoria": cat,
                    "fecha": f,
                    "imagen": extraer_imagen(entry)
                })
        except:
            continue
    return lista

if "pagina" not in st.session_state:
    st.session_state.pagina = 0

with st.spinner("Cargando noticias..."):
    noticias = obtener_noticias(categorias_activas, fecha_desde, fecha_hasta)

if noticias:
    noticias = sorted(noticias, key=lambda x: x["fecha"], reverse=True)
    TAMANO = 5
    total = max(1, (len(noticias) - 1) // TAMANO + 1)
    st.session_state.pagina = max(0, min(st.session_state.pagina, total - 1))
    pagina = noticias[st.session_state.pagina * TAMANO : (st.session_state.pagina + 1) * TAMANO]

    # Primera noticia grande
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

    # Resto en 2 columnas
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

    # Paginación
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

st.markdown("""
<div style="text-align:center;padding:25px 0 10px;color:#888;font-size:12px;border-top:1px solid #ddd;margin-top:30px;">
    Noticias de Argentina
</div>
""", unsafe_allow_html=True)
