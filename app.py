import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Despolarizador de Noticias Argentina",
    page_icon="🇦🇷",
    layout="wide"
)

st.title("🇦🇷 Despolarizador de Noticias - Argentina")
st.caption("Noticias de distintos medios lado a lado • Filtros + Línea de tiempo + Mapa")

# ========== LÍNEA DE TIEMPO ARRIBA ==========
col1, col2, col3, col4 = st.columns([2, 2, 1, 2])

with col1:
    fecha_desde = st.date_input("Desde", value=datetime.now().date() - timedelta(days=3))
with col2:
    fecha_hasta = st.date_input("Hasta", value=datetime.now().date())
with col3:
    if st.button("🕒 Ahora", use_container_width=True):
        fecha_desde = datetime.now().date()
        fecha_hasta = datetime.now().date()
        st.rerun()
with col4:
    st.write("")  # espacio

st.markdown("---")

# ========== FILTROS IZQUIERDA ==========
st.sidebar.header("📂 Filtros de categorías")
st.sidebar.markdown("Marcá las que quieras ver:")

categorias = {
    "Política": st.sidebar.checkbox("Política", value=True),
    "Economía": st.sidebar.checkbox("Economía", value=True),
    "Defensa / Seguridad": st.sidebar.checkbox("Defensa / Seguridad"),
    "Entretenimiento": st.sidebar.checkbox("Entretenimiento"),
    "Debate / Opinión": st.sidebar.checkbox("Debate / Opinión"),
    "Sociedad": st.sidebar.checkbox("Sociedad"),
    "Internacional": st.sidebar.checkbox("Internacional"),
    "Deportes": st.sidebar.checkbox("Deportes"),
}

categorias_activas = [cat for cat, activa in categorias.items() if activa]

# ========== MAPA DE ARGENTINA ==========
st.subheader("🗺️ Mapa de Argentina")

m = folium.Map(
    location=[-38.4161, -63.6167],  # Centro de Argentina
    zoom_start=4,
    tiles="OpenStreetMap"
)

# Marcadores de ejemplo en ciudades importantes (después se pueden asociar a noticias)
ciudades = {
    "Buenos Aires": [-34.6037, -58.3816],
    "Córdoba": [-31.4201, -64.1888],
    "Rosario": [-32.9468, -60.6393],
    "Mendoza": [-32.8895, -68.8458],
    "Salta": [-24.7859, -65.4117],
}

for ciudad, coords in ciudades.items():
    folium.Marker(
        coords,
        popup=ciudad,
        tooltip=ciudad,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

st_folium(m, width=None, height=420)

# ========== NOTICIAS REALES CON RSS ==========
st.subheader("📰 Noticias filtradas")

# Feeds RSS reales de medios argentinos (públicos y gratuitos)
feeds = {
    "Política": [
        "https://www.clarin.com/rss/politica/",
        "https://www.lanacion.com.ar/arc/outboundfeeds/rss/?outputType=xml&_website=la-nacion",
    ],
    "Economía": [
        "https://www.clarin.com/rss/economia/",
        "https://www.ambito.com/rss/pages/economia.xml",
    ],
    "Sociedad": [
        "https://www.clarin.com/rss/sociedad/",
    ],
    "Internacional": [
        "https://www.clarin.com/rss/mundo/",
    ],
    "Entretenimiento": [
        "https://www.clarin.com/rss/espectaculos/",
    ],
    "Deportes": [
        "https://www.clarin.com/rss/deportes/",
    ],
    "Debate / Opinión": [
        "https://www.clarin.com/rss/opinion/",
    ],
}

# Función para traer noticias
@st.cache_data(ttl=600)  # Cache 10 minutos para no saturar
def obtener_noticias(categorias_activas, fecha_desde, fecha_hasta):
    noticias = []
    for cat in categorias_activas:
        if cat in feeds:
            for url in feeds[cat]:
                try:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:8]:  # máximo 8 por feed
                        # Intentamos obtener la fecha
                        try:
                            fecha_noticia = datetime(*entry.published_parsed[:6]).date()
                        except:
                            fecha_noticia = datetime.now().date()

                        if fecha_desde <= fecha_noticia <= fecha_hasta:
                            noticias.append({
                                "titulo": entry.title,
                                "link": entry.link,
                                "medio": feed.feed.get("title", "Medio"),
                                "categoria": cat,
                                "fecha": fecha_noticia
                            })
                except Exception as e:
                    st.warning(f"No se pudo cargar un feed de {cat}")
    return noticias

# Traer y mostrar
with st.spinner("Cargando noticias..."):
    noticias = obtener_noticias(categorias_activas, fecha_desde, fecha_hasta)

if noticias:
    # Ordenar por fecha más reciente
    noticias = sorted(noticias, key=lambda x: x["fecha"], reverse=True)

    for n in noticias:
        st.markdown(f"""
        *{n['titulo']}*  
        📌 {n['medio']} · {n['categoria']} · {n['fecha']}  
        [Leer noticia →]({n['link']})
        """)
        st.markdown("---")
else:
    st.info("No se encontraron noticias con los filtros y fechas seleccionados. Probá ampliar el rango de fechas o activar más categorías.")

# ========== ZÓCALO DE PUBLICIDAD ==========
st.markdown("""
<style>
.banner-ads {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 65px;
    background-color: #f8f9fa;
    border-top: 1px solid #dee2e6;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    font-size: 14px;
    color: #6c757d;
    box-shadow: 0 -2px 8px rgba(0,0,0,0.08);
}
</style>
<div class="banner-ads">
    📢 Espacio publicitario (aquí irá AdSense u otra red de ads • no interrumpe la lectura)
</div>
<div style="height: 75px;"></div>
""", unsafe_allow_html=True)
