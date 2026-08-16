import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import requests

st.set_page_config(page_title="Despolarizador Argentina", page_icon="🇦🇷", layout="wide")

st.title("🇦🇷 Despolarizador de Noticias - Argentina")

# ========== FUNCIÓN PARA TRAER 10 TITULARES DE INFOBAE ==========
@st.cache_data(ttl=300)
def obtener_titulares_infobae():
    urls = [
        "https://www.infobae.com/arc/outboundfeeds/rss/",
        "https://www.infobae.com/argentina/feed/"
    ]
    titulares = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                titulares.append(entry.title)
            if titulares:
                break
        except:
            continue
    if not titulares:
        titulares = ["Cargando titulares de Infobae...", "Revisá más tarde"]
    return titulares[:10]

titulares_banner = obtener_titulares_infobae()
texto_banner = "  •  ".join(titulares_banner)

# ========== BANNER DESPLAZÁNDOSE CON TITULARES DE INFOBAE ==========
st.markdown(f"""
<style>
.marquee {{
    width: 100%;
    overflow: hidden;
    background: #000;
    color: #00ff00;
    padding: 10px 0;
    font-weight: bold;
    font-size: 15px;
    white-space: nowrap;
}}
.marquee span {{
    display: inline-block;
    padding-left: 100%;
    animation: marquee 40s linear infinite;
}}
@keyframes marquee {{
    0% {{ transform: translate(0, 0); }}
    100% {{ transform: translate(-100%, 0); }}
}}
</style>
<div class="marquee">
    <span>🟢 INFOBAE HOY: {texto_banner}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== LÍNEA DE TIEMPO ==========
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    fecha_desde = st.date_input("Desde", value=datetime.now().date() - timedelta(days=2))
with col2:
    fecha_hasta = st.date_input("Hasta", value=datetime.now().date())
with col3:
    if st.button("🕒 Ahora", use_container_width=True):
        st.rerun()

# ========== FILTROS ==========
st.sidebar.header("📂 Categorías")
categorias = {
    "Política": st.sidebar.checkbox("Política", True),
    "Economía": st.sidebar.checkbox("Economía", True),
    "Defensa / Seguridad": st.sidebar.checkbox("Defensa / Seguridad"),
    "Entretenimiento": st.sidebar.checkbox("Entretenimiento"),
    "Debate / Opinión": st.sidebar.checkbox("Debate / Opinión"),
    "Sociedad": st.sidebar.checkbox("Sociedad"),
    "Internacional": st.sidebar.checkbox("Internacional"),
    "Deportes": st.sidebar.checkbox("Deportes"),
}
categorias_activas = [c for c, v in categorias.items() if v]

# ========== MAPA ==========
st.subheader("🗺️ Mapa de Provincias (hacé clic para filtrar noticias de esa provincia)")

@st.cache_data
def cargar_provincias():
    try:
        r = requests.get("https://apis.datos.gob.ar/georef/api/provincias.geojson", timeout=10)
        return r.json()
    except:
        return None

geojson_data = cargar_provincias()

m = folium.Map(location=[-38.4, -63.6], zoom_start=4, tiles="CartoDB positron")

if geojson_data:
    folium.GeoJson(
        geojson_data,
        name="Provincias",
        style_function=lambda x: {"fillColor": "#3388ff", "color": "black", "weight": 1, "fillOpacity": 0.4},
        highlight_function=lambda x: {"fillColor": "#ff7800", "color": "black", "weight": 3, "fillOpacity": 0.7},
        tooltip=folium.Geo
