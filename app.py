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
    geojson_layer = folium.GeoJson(
        data=geojson_data,
        name="Provincias",
        style_function=lambda x: {
            "fillColor": "#3388ff",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.4
        },
        highlight_function=lambda x: {
            "fillColor": "#ff7800",
            "color": "black",
            "weight": 3,
            "fillOpacity": 0.7
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nombre"],
            aliases=["Provincia:"]
        )
    )
    geojson_layer.add_to(m)

map_data = st_folium(m, width=None, height=450, key="mapa")

provincia_seleccionada = None
if map_data and map_data.get("last_object_clicked_tooltip"):
    provincia_seleccionada = map_data["last_object_clicked_tooltip"]
    st.success(f"📍 Filtrando noticias de: *{provincia_seleccionada}*")

# ========== NOTICIAS ==========
st.subheader("📰 Noticias")

feeds = {
    "Política": [
        "https://www.clarin.com/rss/politica/",
        "http://cadena3.com/rss/PoliticayEconomia.xml",
        "https://derechadiario.com.ar/us/rss/cat/argentina"
    ],
    "Economía": [
        "https://www.clarin.com/rss/economia/",
        "http://cadena3.com/rss/PoliticayEconomia.xml"
    ],
    "Sociedad": ["https://www.clarin.com/rss/sociedad/"],
    "Internacional": ["https://www.clarin.com/rss/mundo/"],
    "Entretenimiento": [
        "https://www.clarin.com/rss/espectaculos/",
        "http://cadena3.com/rss/Espectaculos.xml"
    ],
    "Deportes": [
        "https://www.clarin.com/rss/deportes/",
        "http://cadena3.com/rss/Deportes.xml"
    ],
    "Debate / Opinión": ["https://www.clarin.com/rss/opinion/"],
    "Defensa / Seguridad": ["https://www.clarin.com/rss/policiales/"],
}

@st.cache_data(ttl=300)
def obtener_noticias(cats, desde, hasta, provincia=None):
    lista = []
    palabras_graves = [
        "urgente", "último momento", "ultimo momento",
        "alerta", "grave", "tragedia", "muerte", "accidente mortal"
    ]
    
    for cat in cats:
        if cat in feeds:
            for url in feeds[cat]:
                try:
                    feed = feedparser.parse(url)
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
                        
                        es_grave = any(p in titulo.lower() for p in palabras_graves)
                        
                        lista.append({
                            "titulo": titulo,
                            "link": entry.link,
                            "medio": feed.feed.get("title", "Medio")[:40],
                            "categoria": cat,
                            "fecha": f,
                            "grave": es_grave
                        })
                except:
                    pass
    return lista

with st.spinner("Cargando noticias..."):
    noticias = obtener_noticias(
        categorias_activas,
        fecha_desde,
        fecha_hasta,
        provincia_seleccionada
    )

if noticias:
    noticias = sorted(noticias, key=lambda x: x["fecha"], reverse=True)
    for n in noticias:
        if n["grave"]:
            html_grave = f'''
            <div style="background:#fff0f0; padding:10px; border-left:5px solid red; margin-bottom:10px;">
                <span style="color:red; font-weight:bold; font-size:18px;">⚠️ ¡ÚLTIMO MOMENTO!</span><br>
                <span style="color:red; font-size:16px;"><b>{n["titulo"]}</b></span><br>
                <small>{n["medio"]} · {n["categoria"]} · {n["fecha"]}</small><br>
                <a href="{n["link"]}" target="_blank">Leer noticia →</a>
            </div>
            '''
            st.markdown(html_grave, unsafe_allow_html=True)
        else:
            st.markdown(
                f"*{n['titulo']}*  \n"
                f"{n['medio']} · {n['categoria']} · {n['fecha']}  \n"
                f"[Leer →]({n['link']})"
            )
            st.markdown("---")
else:
    st.info("No se encontraron noticias con esos filtros. Probá ampliar fechas o quitar el filtro de provincia.")

# ========== ZÓCALO ==========
st.markdown("""
<style>
.banner-ads {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 55px;
    background: #ffffff;
    border-top: 2px solid #0d6efd;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 99999;
    font-size: 14px;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
}
</style>
<div class="banner-ads">
    📢 Espacio publicitario (AdSense u otra red) — no interrumpe
</div>
<div style="height: 65px;"></div>
""", unsafe_allow_html=True)
