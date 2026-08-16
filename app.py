import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import requests
import re

st.set_page_config(
    page_title="Noticias de Argentina",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== DISEÑO PREMIUM BUENOS AIRES ==========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0c0c0c;
    color: #e8e6e3;
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #f5f0e6 !important;
}

.stApp {
    background: linear-gradient(180deg, #0c0c0c 0%, #141414 100%);
}

section[data-testid="stSidebar"] {
    background: #111111;
    border-right: 1px solid #2a2a2a;
}

.premium-card {
    background: linear-gradient(145deg, #1a1a1a, #151515);
    border: 1px solid #2c2c2c;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.stButton > button {
    background: linear-gradient(135deg, #c9a84c, #a88b3a) !important;
    color: #0c0c0c !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

a { color: #c9a84c !important; }
a:hover { color: #e0c06e !important; }
hr { border-color: #2a2a2a !important; }
</style>
""", unsafe_allow_html=True)

st.title("Noticias de Argentina")

# ========== BANNER INFOBAE ==========
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

st.markdown(f"""
<style>
.marquee {{
    width: 100%;
    overflow: hidden;
    background: #0a0a0a;
    color: #c9a84c;
    padding: 12px 0;
    font-weight: 500;
    font-size: 14px;
    white-space: nowrap;
    border-bottom: 1px solid #2a2a2a;
}}
.marquee span {{
    display: inline-block;
    padding-left: 100%;
    animation: marquee 45s linear infinite;
}}
@keyframes marquee {{
    0% {{ transform: translate(0, 0); }}
    100% {{ transform: translate(-100%, 0); }}
}}
</style>
<div class="marquee">
    <span>INFOBAE HOY · {texto_banner}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== FECHAS ==========
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    fecha_desde = st.date_input("Desde", value=datetime.now().date() - timedelta(days=2))
with col2:
    fecha_hasta = st.date_input("Hasta", value=datetime.now().date())
with col3:
    if st.button("Ahora", use_container_width=True):
        st.rerun()

# ========== SIDEBAR ==========
st.sidebar.header("Categorías")
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
st.subheader("Mapa de Provincias")
st.caption("Hacé clic en una provincia para filtrar noticias locales")

@st.cache_data
def cargar_provincias():
    try:
        r = requests.get("https://apis.datos.gob.ar/georef/api/provincias.geojson", timeout=10)
        return r.json()
    except:
        return None

geojson_data = cargar_provincias()

m = folium.Map(location=[-38.4, -63.6], zoom_start=4, tiles="CartoDB dark_matter")

if geojson_data:
    geojson_layer = folium.GeoJson(
        data=geojson_data,
        name="Provincias",
        style_function=lambda x: {
            "fillColor": "#c9a84c",
            "color": "#1a1a1a",
            "weight": 1.2,
            "fillOpacity": 0.35
        },
        highlight_function=lambda x: {
            "fillColor": "#e0c06e",
            "color": "#c9a84c",
            "weight": 2.5,
            "fillOpacity": 0.65
        },
        tooltip=folium.GeoJsonTooltip(fields=["nombre"], aliases=["Provincia:"])
    )
    geojson_layer.add_to(m)

map_data = st_folium(m, width=None, height=420, key="mapa")

provincia_seleccionada = None
if map_data and map_data.get("last_object_clicked_tooltip"):
    raw = map_data["last_object_clicked_tooltip"]
    provincia_seleccionada = re.sub(r'(?i)^Provincia:\s*', '', str(raw)).strip()
    st.success(f"Filtrando noticias de: **{provincia_seleccionada}**")

# ========== DIARIOS PROVINCIALES ==========
DIARIOS_PROVINCIALES = {
    "Buenos Aires": ["https://www.eldia.com/rss", "https://www.lanueva.com/rss"],
    "Ciudad Autónoma de Buenos Aires": ["https://www.clarin.com/rss/lo-ultimo/", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/?outputType=xml"],
    "Catamarca": ["https://www.elancasti.com.ar/rss"],
    "Chaco": ["https://www.diarionorte.com/rss"],
    "Chubut": ["https://www.elchubut.com.ar/rss", "https://www.diariojornada.com.ar/rss"],
    "Córdoba": ["https://www.lavoz.com.ar/rss"],
    "Corrientes": ["https://www.ellitoral.com.ar/rss"],
    "Entre Ríos": ["https://www.unoentrerios.com.ar/rss"],
    "Formosa": ["https://www.diariolaformosa.com/rss"],
    "Jujuy": ["https://www.eltribuno.com/jujuy/rss"],
    "La Pampa": ["https://www.laarena.com.ar/rss"],
    "La Rioja": ["https://www.elindependiente.com.ar/rss"],
    "Mendoza": ["https://www.losandes.com.ar/rss", "https://www.diariouno.com.ar/rss"],
    "Misiones": ["https://www.misionesonline.net/feed", "https://www.elterritorio.com.ar/rss/ahora/"],
    "Neuquén": ["https://www.lmneuquen.com/rss", "https://www.rionegro.com.ar/feed/"],
    "Río Negro": ["https://www.rionegro.com.ar/feed/"],
    "Salta": ["https://www.eltribuno.com/salta/rss"],
    "San Juan": ["https://www.diariodecuyo.com.ar/rss"],
    "San Luis": ["https://www.eldiariodelarepublica.com/rss"],
    "Santa Cruz": ["https://www.laopinionaustral.com.ar/rss"],
    "Santa Fe": ["https://www.lacapital.com.ar/rss", "https://www.ellitoral.com/rss"],
    "Santiago del Estero": ["https://www.elliberal.com.ar/rss", "https://www.diariopanorama.com/rss"],
    "Tierra del Fuego": ["https://www.surenio.com.ar/rss"],
    "Tucumán": ["https://www.lagaceta.com.ar/rss", "https://feeds.feedburner.com/LaGaceta"],
}

# ========== FUNCIÓN MEJORADA PARA EXTRAER IMÁGENES ==========
def extraer_imagen(entry) -> str | None:
    # 1. media_content
    if hasattr(entry, "media_content") and entry.media_content:
        for m in entry.media_content:
            url = m.get("url")
            if url and ("image" in m.get("type", "") or url.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))):
                return url
        if entry.media_content[0].get("url"):
            return entry.media_content[0]["url"]

    # 2. media_thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get("url")
        if url:
            return url

    # 3. enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            url = enc.get("href") or enc.get("url")
            if url and (enc.get("type", "").startswith("image") or url.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))):
                return url

    # 4. links
    if hasattr(entry, "links"):
        for link in entry.links:
            if link.get("type", "").startswith("image") or (link.get("href", "").lower().endswith((".jpg", ".jpeg", ".png", ".webp"))):
                return link.get("href")

    # 5. Buscar en summary / content (HTML)
    content = ""
    if entry.get("content"):
        content = entry.content[0].get("value", "")
    elif entry.get("summary"):
        content = entry.summary
    elif entry.get("description"):
        content = entry.description

    if content:
        # Busca src de img
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # A veces viene como data-src
        match = re.search(r'data-src=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if match:
            return match.group(1)

    return None

# ========== NOTICIA DEL DÍA + TN VIVO ==========
st.markdown("---")
st.subheader("Destacados")

@st.cache_data(ttl=300)
def obtener_noticia_infobae():
    try:
        feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
        if feed.entries:
            entry = feed.entries[0]
            return {
                "titulo": entry.title,
                "link": entry.link,
                "imagen": extraer_imagen(entry)
            }
    except:
        pass
    return None

noticia_infobae = obtener_noticia_infobae()

col_infobae, col_tn = st.columns(2)

with col_infobae:
    if noticia_infobae:
        n = noticia_infobae
        st.markdown(f"""
        <div class="premium-card">
            <div style="color:#c9a84c; font-size:12px; font-weight:600; letter-spacing:1px; margin-bottom:12px;">
                INFOBAE · NOTICIA DEL DÍA
            </div>
            {"<img src='" + n['imagen'] + "' style='width:100%; max-height:200px; object-fit:cover; border-radius:10px; margin-bottom:16px;' onerror=\"this.style.display='none'\">" if n.get("imagen") else ""}
            <div style="font-family:'Playfair Display',serif; font-size:22px; font-weight:600; line-height:1.3; color:#f5f0e6; margin-bottom:16px;">
                {n['titulo']}
            </div>
            <a href="{n['link']}" target="_blank" style="
                display:inline-block;
                background:linear-gradient(135deg,#c9a84c,#a88b3a);
                color:#0c0c0c !important;
                padding:10px 20px;
                border-radius:8px;
                font-weight:600;
                font-size:13px;
            ">Leer en Infobae</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No se pudo cargar la noticia de Infobae")

with col_tn:
    st.markdown("""
    <div class="premium-card">
        <div style="color:#c9a84c; font-size:12px; font-weight:600; letter-spacing:1px; margin-bottom:12px;">
            TN · TRANSMISIÓN EN VIVO
        </div>
        <div style="position:relative; padding-bottom:56.25%; height:0; overflow:hidden; border-radius:10px;">
            <iframe 
                src="https://www.youtube.com/embed/live_stream?channel=UCj6PcyLvpnIRT_2W_mwa9Aw&autoplay=1&mute=0" 
                style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        </div>
        <div style="margin-top:12px; font-size:12px; color:#888;">
            Señal oficial 24 hs · Todo Noticias
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== NOTICIAS ==========
st.subheader("Últimas Noticias")

TN_FEED = "https://tn.com.ar/arc/outboundfeeds/google-news-feed/?outputType=xml"

def detectar_categoria_tn(link: str) -> str:
    link = link.lower()
    if "/politica/" in link: return "Política"
    if "/economia/" in link or "/finanzas/" in link: return "Economía"
    if "/sociedad/" in link: return "Sociedad"
    if "/internacional/" in link or "/mundo/" in link: return "Internacional"
    if "/show/" in link or "/espectaculos/" in link: return "Entretenimiento"
    if "/deportes/" in link: return "Deportes"
    if "/opinion/" in link: return "Debate / Opinión"
    if "/policiales/" in link or "/seguridad/" in link: return "Defensa / Seguridad"
    return "Sociedad"

feeds_extra = {
    "Política": ["http://cadena3.com/rss/PoliticayEconomia.xml"],
    "Economía": ["http://cadena3.com/rss/PoliticayEconomia.xml"],
    "Entretenimiento": ["http://cadena3.com/rss/Espectaculos.xml"],
    "Deportes": ["http://cadena3.com/rss/Deportes.xml", "https://www.ole.com.ar/rss/ultimas-noticias/"],
}

@st.cache_data(ttl=300)
def obtener_noticias(cats, desde, hasta, provincia=None):
    lista = []
    palabras_graves = ["urgente", "último momento", "ultimo momento", "alerta", "grave", "tragedia", "muerte"]

    fuentes = [TN_FEED]
    for cat in cats:
        if cat in feeds_extra:
            fuentes.extend(feeds_extra[cat])

    if provincia and provincia in DIARIOS_PROVINCIALES:
        fuentes.extend(DIARIOS_PROVINCIALES[provincia])

    for url in set(fuentes):
        try:
            feed = feedparser.parse(url)
            medio_nombre = feed.feed.get("title", "Medio")[:40]
            for entry in feed.entries[:12]:
                try:
                    f = datetime(*entry.published_parsed[:6]).date()
                except:
                    f = datetime.now().date()

                if not (desde <= f <= hasta):
                    continue

                titulo = entry.title

                # Filtro provincia
                if provincia:
                    es_diario_provincial = url in DIARIOS_PROVINCIALES.get(provincia, [])
                    if not es_diario_provincial and provincia.lower() not in titulo.lower():
                        continue

                if "tn.com.ar" in url:
                    cat = detectar_categoria_tn(entry.link)
                    if cat not in cats:
                        continue
                else:
                    cat = "Sociedad"

                es_grave = any(p in titulo.lower() for p in palabras_graves)
                imagen = extraer_imagen(entry)

                lista.append({
                    "titulo": titulo,
                    "link": entry.link,
                    "medio": medio_nombre,
                    "categoria": cat,
                    "fecha": f,
                    "grave": es_grave,
                    "imagen": imagen
                })
        except:
            continue

    return lista

# ========== PAGINACIÓN + FOTOS ==========
if "pagina" not in st.session_state:
    st.session_state.pagina = 0

with st.spinner("Cargando noticias..."):
    noticias = obtener_noticias(categorias_activas, fecha_desde, fecha_hasta, provincia_seleccionada)

if noticias:
    noticias = sorted(noticias, key=lambda x: x["fecha"], reverse=True)

    TAMANO_PAGINA = 5
    total_paginas = max(1, (len(noticias) - 1) // TAMANO_PAGINA + 1)
    st.session_state.pagina = max(0, min(st.session_state.pagina, total_paginas - 1))

    inicio = st.session_state.pagina * TAMANO_PAGINA
    fin = inicio + TAMANO_PAGINA
    noticias_pagina = noticias[inicio:fin]

    # ========== AQUÍ SE MUESTRAN LAS 5 FOTOS ==========
    for n in noticias_pagina:
        col_img, col_txt = st.columns([1.1, 4.9])

        with col_img:
            if n.get("imagen"):
                st.markdown(
                    f'''
                    <img src="{n["imagen"]}" 
                         width="130" 
                         height="90"
                         style="width:130px; height:90px; object-fit:cover; border-radius:10px; display:block; border:1px solid #2a2a2a;"
                         loading="lazy"
                         onerror="this.src='https://via.placeholder.com/130x90/1a1a1a/555555?text=Sin+foto'; this.onerror=null;">
                    ''',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '''
                    <div style="width:130px; height:90px; background:#1a1a1a; 
                                border-radius:10px; display:flex; align-items:center; 
                                justify-content:center; color:#555; font-size:12px; border:1px solid #2a2a2a;">
                        Sin foto
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

        with col_txt:
            if n["grave"]:
                st.markdown(
                    f"""
                    <div style="border-left:3px solid #c9a84c; padding-left:14px; margin-bottom:6px;">
                        <span style="color:#c9a84c; font-size:12px; font-weight:600;">⚠️ ÚLTIMO MOMENTO</span><br>
                        <b style="font-size:16px; color:#f5f0e6; line-height:1.35;">{n['titulo']}</b><br>
                        <small style="color:#888;">{n['medio']} · {n['categoria']} · {n['fecha']}</small><br>
                        <a href="{n['link']}" target="_blank" style="font-size:13px;">Leer →</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="padding:2px 0 8px 0;">
                        <b style="font-size:16px; color:#f5f0e6; line-height:1.35;">{n['titulo']}</b><br>
                        <small style="color:#888;">{n['medio']} · {n['categoria']} · {n['fecha']}</small> · 
                        <a href="{n['link']}" target="_blank" style="font-size:13px;">Leer →</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Paginación
    st.markdown("---")
    col_ant, col_info, col_sig = st.columns([1, 2, 1])

    with col_ant:
        if st.button("← Anterior", use_container_width=True, disabled=(st.session_state.pagina == 0)):
            st.session_state.pagina -= 1
            st.rerun()

    with col_info:
        st.markdown(
            f"<div style='text-align:center; padding-top:8px; color:#aaa;'>Página <b>{st.session_state.pagina + 1}</b> de <b>{total_paginas}</b></div>",
            unsafe_allow_html=True
        )

    with col_sig:
        if st.button("Siguiente →", use_container_width=True, disabled=(st.session_state.pagina >= total_paginas - 1)):
            st.session_state.pagina += 1
            st.rerun()

else:
    st.info("No se encontraron noticias con esos filtros.")

# Footer
st.markdown("""
<div style="height:30px;"></div>
<div style="text-align:center; padding:16px 0; border-top:1px solid #2a2a2a; color:#555; font-size:12px;">
    Noticias de Argentina · Diseño premium · Buenos Aires
</div>
""", unsafe_allow_html=True)
