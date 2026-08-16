import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import requests
import re
from collections import defaultdict

# Intentamos importar yfinance (opcional)
try:
    import yfinance as yf
    YFINANCE_OK = True
except:
    YFINANCE_OK = False

st.set_page_config(
    page_title="Noticias de Argentina",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== DISEÑO ESTILO DIARIO (fondo claro + tipografía NYT) ==========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #f8f6f2;
    color: #1a1a1a;
}

h1, h2, h3, .stTitle {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #111 !important;
    letter-spacing: -0.4px;
}

.stApp {
    background-color: #f8f6f2;
}

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e0ddd6;
}

.stButton > button {
    background: #1a1a1a !important;
    color: white !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
}

a { color: #8B0000 !important; text-decoration: none !important; }
a:hover { text-decoration: underline !important; }

hr { border-color: #ddd !important; }

.noticia-card {
    background: white;
    border: 1px solid #e5e2db;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.logo-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 110px;
    height: 75px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 18px;
    color: white;
    text-align: center;
    line-height: 1.1;
}
</style>
""", unsafe_allow_html=True)

st.title("Noticias de Argentina")

# ========== LOGOS DE FUENTES (badge generado) ==========
LOGOS = {
    "TN": {"color": "#00a0e3", "texto": "TN"},
    "Infobae": {"color": "#e63946", "texto": "INFO\nBAE"},
    "Cadena 3": {"color": "#1a73e8", "texto": "C3"},
    "La Nación": {"color": "#000000", "texto": "LA\nNACIÓN"},
    "Clarín": {"color": "#c8102e", "texto": "CLARÍN"},
    "Olé": {"color": "#ff6600", "texto": "OLÉ"},
    "Infodefensa": {"color": "#2c3e50", "texto": "INFO\nDEFENSA"},
    "La Gaceta": {"color": "#8B0000", "texto": "LA\nGACETA"},
    "Los Andes": {"color": "#1a5276", "texto": "LOS\nANDES"},
    "default": {"color": "#555555", "texto": "MEDIO"}
}

def get_logo_html(medio: str) -> str:
    key = "default"
    for k in LOGOS:
        if k.lower() in medio.lower():
            key = k
            break
    logo = LOGOS[key]
    return f'''
    <div class="logo-badge" style="background:{logo['color']};">
        {logo['texto'].replace(chr(10), '<br>')}
    </div>
    '''

# ========== BANNER ==========
@st.cache_data(ttl=300)
def obtener_titulares_infobae():
    try:
        feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
        return [e.title for e in feed.entries[:8]]
    except:
        return ["Cargando..."]

texto_banner = "  •  ".join(obtener_titulares_infobae())

st.markdown(f"""
<div style="background:#111; color:#f5f0e6; padding:10px 0; font-size:13px; white-space:nowrap; overflow:hidden;">
    <div style="display:inline-block; padding-left:100%; animation: marquee 40s linear infinite;">
        INFOBAE HOY · {texto_banner}
    </div>
</div>
<style>
@keyframes marquee {{
    0% {{ transform: translateX(0); }}
    100% {{ transform: translateX(-100%); }}
}}
</style>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== FECHAS ==========
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    fecha_desde = st.date_input("Desde", value=datetime.now().date() - timedelta(days=2))
with col2:
    fecha_hasta = st.date_input("Hasta", value=datetime.now().date())
with col3:
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

# ========== MAPA + BOLSA (lado a lado) ==========
col_mapa, col_bolsa = st.columns([1.4, 1])

with col_mapa:
    st.subheader("Provincias")
    @st.cache_data
    def cargar_provincias():
        try:
            r = requests.get("https://apis.datos.gob.ar/georef/api/provincias.geojson", timeout=8)
            return r.json()
        except:
            return None

    geojson_data = cargar_provincias()
    m = folium.Map(location=[-38.4, -63.6], zoom_start=3.8, tiles="CartoDB positron")
    if geojson_data:
        folium.GeoJson(
            geojson_data,
            style_function=lambda x: {"fillColor": "#8B0000", "color": "#333", "weight": 1, "fillOpacity": 0.3},
            highlight_function=lambda x: {"fillColor": "#c0392b", "weight": 2, "fillOpacity": 0.55},
            tooltip=folium.GeoJsonTooltip(fields=["nombre"], aliases=["Provincia:"])
        ).add_to(m)
    map_data = st_folium(m, width=None, height=320, key="mapa")

    provincia_seleccionada = None
    if map_data and map_data.get("last_object_clicked_tooltip"):
        raw = map_data["last_object_clicked_tooltip"]
        provincia_seleccionada = re.sub(r'(?i)^Provincia:\s*', '', str(raw)).strip()
        st.success(f"Filtrando: **{provincia_seleccionada}**")

with col_bolsa:
    st.subheader("Mercados")
    st.caption("EE.UU. y Argentina")

    if YFINANCE_OK:
        try:
            tickers = {
                "S&P 500": "^GSPC",
                "Dow Jones": "^DJI",
                "Nasdaq": "^IXIC",
                "Merval": "^MERV",
                "YPF": "YPF",
                "Galicia": "GGAL"
            }
            for nombre, ticker in tickers.items():
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if not hist.empty:
                    precio = hist["Close"].iloc[-1]
                    cambio = ((hist["Close"].iloc[-1] / hist["Close"].iloc[-2]) - 1) * 100
                    color = "green" if cambio >= 0 else "red"
                    st.markdown(
                        f"""
                        <div style="background:white; border:1px solid #e5e2db; border-radius:6px; 
                                    padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between;">
                            <span style="font-weight:600;">{nombre}</span>
                            <span>
                                <b>{precio:,.2f}</b> 
                                <span style="color:{color}; font-size:13px;">({cambio:+.2f}%)</span>
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.write(f"{nombre}: sin datos")
        except Exception as e:
            st.info("No se pudieron cargar los datos de mercados en este momento.")
    else:
        st.info("Instalá `yfinance` para ver la bolsa en vivo:\n`pip install yfinance`")

st.markdown("---")

# ========== DESTACADOS ==========
st.subheader("Destacados del día")

def extraer_imagen(entry):
    if hasattr(entry, "media_content") and entry.media_content:
        for m in entry.media_content:
            url = m.get("url")
            if url and url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                return url
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    content = entry.get("summary", "") or (entry.content[0].value if entry.get("content") else "")
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
    return match.group(1) if match else None

@st.cache_data(ttl=300)
def obtener_noticia_infobae():
    try:
        feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
        if feed.entries:
            e = feed.entries[0]
            return {"titulo": e.title, "link": e.link, "imagen": extraer_imagen(e)}
    except:
        return None

n_infobae = obtener_noticia_infobae()

col1, col2 = st.columns(2)
with col1:
    if n_infobae:
        st.markdown(f"""
        <div class="noticia-card">
            <div style="font-size:11px; color:#8B0000; font-weight:600; margin-bottom:8px;">INFOBAE · DESTACADA</div>
            {"<img src='" + n_infobae['imagen'] + "' style='width:100%; max-height:180px; object-fit:cover; border-radius:4px; margin-bottom:12px;'>" if n_infobae.get("imagen") else ""}
            <div style="font-family:'Playfair Display',serif; font-size:20px; font-weight:700; line-height:1.3;">
                {n_infobae['titulo']}
            </div>
            <a href="{n_infobae['link']}" target="_blank" style="font-size:13px;">Leer →</a>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="noticia-card">
        <div style="font-size:11px; color:#00a0e3; font-weight:600; margin-bottom:8px;">TN · EN VIVO</div>
        <div style="position:relative; padding-bottom:56.25%; height:0;">
            <iframe src="https://www.youtube.com/embed/live_stream?channel=UCj6PcyLvpnIRT_2W_mwa9Aw&autoplay=0" 
                    style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;" 
                    allowfullscreen></iframe>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== NOTICIAS (layout tipo diario) ==========
st.subheader("Últimas noticias")

TN_FEED = "https://tn.com.ar/arc/outboundfeeds/google-news-feed/?outputType=xml"

feeds_extra = {
    "Política": ["http://cadena3.com/rss/PoliticayEconomia.xml"],
    "Economía": ["http://cadena3.com/rss/PoliticayEconomia.xml"],
    "Defensa / Seguridad": [
        "https://www.infodefensa.com/rss.php",
        "http://cadena3.com/rss/PoliticayEconomia.xml"
    ],
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
def obtener_noticias(cats, desde, hasta, provincia=None):
    lista = []
    fuentes = [TN_FEED]
    for c in cats:
        fuentes.extend(feeds_extra.get(c, []))

    for url in set(fuentes):
        try:
            feed = feedparser.parse(url)
            medio = feed.feed.get("title", "Medio")[:35]
            for entry in feed.entries[:12]:
                try:
                    f = datetime(*entry.published_parsed[:6]).date()
                except:
                    f = datetime.now().date()
                if not (desde <= f <= hasta):
                    continue
                titulo = entry.title
                if provincia and provincia.lower() not in titulo.lower():
                    continue
                cat = detectar_categoria_tn(entry.link) if "tn.com.ar" in url else "Sociedad"
                if cat not in cats and "tn.com.ar" in url:
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

with st.spinner("Cargando..."):
    noticias = obtener_noticias(categorias_activas, fecha_desde, fecha_hasta, provincia_seleccionada)

if noticias:
    noticias = sorted(noticias, key=lambda x: x["fecha"], reverse=True)
    TAMANO = 5
    total_pag = max(1, (len(noticias)-1)//TAMANO + 1)
    st.session_state.pagina = max(0, min(st.session_state.pagina, total_pag-1))
    pagina_noticias = noticias[st.session_state.pagina*TAMANO : (st.session_state.pagina+1)*TAMANO]

    # ===== LAYOUT TIPO DIARIO =====
    # Primera noticia grande (destacada)
    if len(pagina_noticias) > 0:
        n = pagina_noticias[0]
        col_img, col_txt = st.columns([1.3, 2.7])
        with col_img:
            if n.get("imagen"):
                st.image(n["imagen"], use_container_width=True)
            else:
                st.markdown(get_logo_html(n["medio"]), unsafe_allow_html=True)
        with col_txt:
            st.markdown(f"""
            <div style="font-size:12px; color:#8B0000; font-weight:600; margin-bottom:6px;">{n['medio'].upper()} · {n['categoria']}</div>
            <div style="font-family:'Playfair Display',serif; font-size:26px; font-weight:700; line-height:1.25; margin-bottom:10px;">
                {n['titulo']}
            </div>
            <a href="{n['link']}" target="_blank">Leer nota completa →</a>
            """, unsafe_allow_html=True)
        st.markdown("---")

    # Resto en grilla 2 columnas
    resto = pagina_noticias[1:]
    if resto:
        cols = st.columns(2)
        for i, n in enumerate(resto):
            with cols[i % 2]:
                st.markdown(f"""
                <div class="noticia-card">
                    <div style="display:flex; gap:12px; align-items:flex-start;">
                        <div>
                            {f'<img src="{n["imagen"]}" style="width:90px; height:65px; object-fit:cover; border-radius:4px;">' if n.get("imagen") else get_logo_html(n["medio"])}
                        </div>
                        <div>
                            <div style="font-size:11px; color:#666; margin-bottom:4px;">{n['medio']} · {n['fecha']}</div>
                            <div style="font-family:'Playfair Display',serif; font-size:16px; font-weight:600; line-height:1.3;">
                                <a href="{n['link']}" target="_blank" style="color:#111 !important;">{n['titulo']}</a>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Paginación
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("← Anterior", disabled=st.session_state.pagina==0):
            st.session_state.pagina -= 1
            st.rerun()
    with c2:
        st.markdown(f"<div style='text-align:center; padding-top:8px;'>Página {st.session_state.pagina+1} de {total_pag}</div>", unsafe_allow_html=True)
    with c3:
        if st.button("Siguiente →", disabled=st.session_state.pagina >= total_pag-1):
            st.session_state.pagina += 1
            st.rerun()
else:
    st.info("No se encontraron noticias con esos filtros.")

st.markdown("""
<div style="text-align:center; padding:30px 0 10px; color:#888; font-size:12px; border-top:1px solid #ddd; margin-top:40px;">
    Noticias de Argentina · Estilo diario · Buenos Aires
</div>
""", unsafe_allow_html=True)
