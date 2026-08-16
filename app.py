import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import requests
import re

# Intentamos importar yfinance
try:
    import yfinance as yf
    YFINANCE_OK = True
except ImportError:
    YFINANCE_OK = False

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

h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #111 !important;
}

.stApp {
    background-color: #f7f5f0;
}

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e2db;
}

.stButton > button {
    background: #1a1a1a !important;
    color: white !important;
    border-radius: 4px !important;
}

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
}
</style>
""", unsafe_allow_html=True)

st.title("Noticias de Argentina")

# ========== LOGOS ==========
LOGOS = {
    "TN": {"color": "#00a0e3", "texto": "TN"},
    "Infobae": {"color": "#e63946", "texto": "INFOBAE"},
    "Cadena 3": {"color": "#1a73e8", "texto": "C3"},
    "La Nación": {"color": "#111", "texto": "LA NACIÓN"},
    "Clarín": {"color": "#c8102e", "texto": "CLARÍN"},
    "Olé": {"color": "#ff6600", "texto": "OLÉ"},
    "Infodefensa": {"color": "#2c3e50", "texto": "INFODEFENSA"},
    "default": {"color": "#555", "texto": "MEDIO"}
}

def get_logo_html(medio: str) -> str:
    key = "default"
    for k in LOGOS:
        if k.lower() in medio.lower():
            key = k
            break
    logo = LOGOS[key]
    return f'<div class="logo-badge" style="background:{logo["color"]};">{logo["texto"]}</div>'

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

# ========== MAPA + BOLSA ==========
col_mapa, col_bolsa = st.columns([1.45, 1])

with col_mapa:
    st.subheader("Provincias")
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
        st.success(f"Filtrando: **{provincia_seleccionada}**")

with col_bolsa:
    st.subheader("Mercados")
    st.caption("EE.UU. · Argentina")

    if YFINANCE_OK:
        try:
            data = {
                "S&P 500": yf.Ticker("^GSPC").history(period="5d"),
                "Dow Jones": yf.Ticker("^DJI").history(period="5d"),
                "Nasdaq": yf.Ticker("^IXIC").history(period="5d"),
                "Merval": yf.Ticker("^MERV").history(period="5d"),
                "YPF": yf.Ticker("YPF").history(period="5d"),
                "Galicia": yf.Ticker("GGAL").history(period="5d"),
            }
            for nombre, hist in data.items():
                if not hist.empty and len(hist) >= 2:
                    precio = hist["Close"].iloc[-1]
                    cambio = ((hist["Close"].iloc[-1] / hist["Close"].iloc[-2]) - 1) * 100
                    color = "#14804A" if cambio >= 0 else "#C0392B"
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #e5e2db;border-radius:6px;
                                padding:9px 12px;margin-bottom:7px;display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:600;font-size:14px;">{nombre}</span>
                        <span>
                            <b style="font-size:14px;">{precio:,.2f}</b>
                            <span style="color:{color};font-size:12px;margin-left:6px;">({cambio:+.2f}%)</span>
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write(f"{nombre}: sin datos")
        except Exception:
            st.warning("Error al obtener datos de mercado. Intentá más tarde.")
    else:
        # Versión de respaldo (sin yfinance)
        st.markdown("""
        <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:6px;padding:12px;font-size:13px;">
            <b>Para ver la bolsa en vivo</b><br>
            Ejecutá en la terminal:<br>
            <code>pip install yfinance</code><br><br>
            Luego reiniciá la app.
        </div>
        """, unsafe_allow_html=True)

        # Datos estáticos de ejemplo para que no quede vacío
        ejemplo = [
            ("S&P 500", "5.890", "+0.42%"),
            ("Dow Jones", "42.150", "+0.28%"),
            ("Nasdaq", "19.320", "+0.65%"),
            ("Merval", "2.145.000", "-0.35%"),
            ("YPF", "28.450", "+1.12%"),
            ("Galicia", "6.820", "-0.80%"),
        ]
        for nombre, precio, cambio in ejemplo:
            color = "#14804A" if "+" in cambio else "#C0392B"
            st.markdown(f"""
            <div style="background:white;border:1px solid #e5e2db;border-radius:6px;
                        padding:9px 12px;margin-bottom:7px;display:flex;justify-content:space-between;">
                <span style="font-weight:600;">{nombre}</span>
                <span><b>{precio}</b> <span style="color:{color};font-size:12px;">{cambio}</span></span>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

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
        st.markdown('<div style="font-size:11px;color:#8B0000;font-weight:600;margin-bottom:8px;">INFOBAE · DESTACADA</div>', unsafe_allow_html=True)
        
        if n_infobae.get("imagen"):
            st.image(n_infobae["imagen"], use_container_width=True)
        else:
            st.markdown(get_logo_html("Infobae"), unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="font-family:'Playfair Display',serif;font-size:20px;font-weight:700;line-height:1.3;margin:12px 0;">
            {n_infobae['titulo']}
        </div>
        <a href="{n_infobae['link']}" target="_blank">Leer en Infobae →</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No se pudo cargar la noticia de Infobae")

with col_b:
    st.markdown("""
    <div class="noticia-card">
        <div style="font-size:11px;color:#00a0e3;font-weight:600;margin-bottom:8px;">TN · TRANSMISIÓN EN VIVO</div>
        <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:4px;">
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
def obtener_noticias(cats, desde, hasta, provincia=None):
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
                if provincia and provincia.lower() not in titulo.lower():
                    continue
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
    noticias = obtener_noticias(categorias_activas, fecha_desde, fecha_hasta, provincia_seleccionada)

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
            <div style="font-size:12px;color:#8B0000;font-weight:600;margin-bottom:6px;">
                {n['medio'].upper()} · {n['categoria']}
            </div>
            <div style="font-family:'Playfair Display',serif;font-size:24px;font-weight:700;line-height:1.25;margin-bottom:10px;">
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
                        <div style="font-size:11px;color:#666;margin-bottom:4px;">{n['medio']} · {n['fecha']}</div>
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
        st.markdown(f"<div style='text-align:center;padding-top:8px;'>Página {st.session_state.pagina+1} de {total}</div>", unsafe_allow_html=True)
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
