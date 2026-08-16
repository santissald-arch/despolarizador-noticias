import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import feedparser
import requests
import re

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

# ========== BANNER DESPLAZÁNDOSE ==========
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
    raw = map_data["last_object_clicked_tooltip"]
    # Limpiamos el prefijo "Provincia: "
    provincia_seleccionada = re.sub(r'(?i)^Provincia:\s*', '', str(raw)).strip()
    st.success(f"📍 Filtrando noticias de: **{provincia_seleccionada}**")

# ========== NOTICIA DEL DÍA (INFOBAE + TN) ==========
st.markdown("---")
st.subheader("🔥 Noticia del día")

def extraer_imagen(entry) -> str | None:
    if hasattr(entry, "media_content") and entry.media_content:
        for m in entry.media_content:
            url = m.get("url")
            if url and (m.get("type", "").startswith("image") or url.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))):
                return url
        if entry.media_content[0].get("url"):
            return entry.media_content[0]["url"]

    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")

    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            url = enc.get("href") or enc.get("url")
            if url and (enc.get("type", "").startswith("image") or url.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))):
                return url

    content = ""
    if entry.get("content"):
        content = entry.content[0].get("value", "")
    elif entry.get("summary"):
        content = entry.summary

    if content:
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if match:
            return match.group(1)

    return None

@st.cache_data(ttl=300)
def obtener_noticia_del_dia():
    resultado = {"infobae": None, "tn": None}

    # Infobae
    try:
        feed = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/")
        if feed.entries:
            entry = feed.entries[0]
            resultado["infobae"] = {
                "titulo": entry.title,
                "link": entry.link,
                "imagen": extraer_imagen(entry),
                "medio": "Infobae"
            }
    except:
        pass

    # TN
    try:
        feed = feedparser.parse("https://tn.com.ar/arc/outboundfeeds/google-news-feed/?outputType=xml")
        if feed.entries:
            entry = feed.entries[0]
            resultado["tn"] = {
                "titulo": entry.title,
                "link": entry.link,
                "imagen": extraer_imagen(entry),
                "medio": "TN"
            }
    except:
        pass

    return resultado

noticias_dia = obtener_noticia_del_dia()

col_infobae, col_tn = st.columns(2)

with col_infobae:
    if noticias_dia["infobae"]:
        n = noticias_dia["infobae"]
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            padding: 20px;
            height: 100%;
            border-left: 6px solid #e63946;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        ">
            <div style="color:#e63946; font-weight:700; font-size:14px; margin-bottom:8px;">
                🔴 INFOBAE · NOTICIA DEL DÍA
            </div>
            {"<img src='" + n['imagen'] + "' style='width:100%; max-height:180px; object-fit:cover; border-radius:8px; margin-bottom:12px;' onerror=\"this.style.display='none'\">" if n.get("imagen") else ""}
            <div style="font-size:22px; font-weight:700; line-height:1.3; color:white; margin-bottom:12px;">
                {n['titulo']}
            </div>
            <a href="{n['link']}" target="_blank" style="
                display:inline-block;
                background:#e63946;
                color:white;
                padding:8px 16px;
                border-radius:6px;
                text-decoration:none;
                font-weight:600;
                font-size:14px;
            ">Leer en Infobae →</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No se pudo cargar la noticia de Infobae")

with col_tn:
    if noticias_dia["tn"]:
        n = noticias_dia["tn"]
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #0f0f0f 0%, #1c1c1c 100%);
            border-radius: 12px;
            padding: 20px;
            height: 100%;
            border-left: 6px solid #00b4d8;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        ">
            <div style="color:#00b4d8; font-weight:700; font-size:14px; margin-bottom:8px;">
                🔵 TN · NOTICIA DEL DÍA
            </div>
            {"<img src='" + n['imagen'] + "' style='width:100%; max-height:180px; object-fit:cover; border-radius:8px; margin-bottom:12px;' onerror=\"this.style.display='none'\">" if n.get("imagen") else ""}
            <div style="font-size:22px; font-weight:700; line-height:1.3; color:white; margin-bottom:12px;">
                {n['titulo']}
            </div>
            <a href="{n['link']}" target="_blank" style="
                display:inline-block;
                background:#00b4d8;
                color:white;
                padding:8px 16px;
                border-radius:6px;
                text-decoration:none;
                font-weight:600;
                font-size:14px;
            ">Leer en TN →</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No se pudo cargar la noticia de TN")

st.markdown("---")

# ========== NOTICIAS ==========
st.subheader("📰 Noticias")

TN_FEED = "https://tn.com.ar/arc/outboundfeeds/google-news-feed/?outputType=xml"

def detectar_categoria_tn(link: str) -> str:
    link = link.lower()
    if "/politica/" in link:
        return "Política"
    if "/economia/" in link or "/finanzas/" in link:
        return "Economía"
    if "/sociedad/" in link:
        return "Sociedad"
    if "/internacional/" in link or "/mundo/" in link:
        return "Internacional"
    if "/show/" in link or "/espectaculos/" in link or "/entretenimiento/" in link:
        return "Entretenimiento"
    if "/deportes/" in link:
        return "Deportes"
    if "/opinion/" in link:
        return "Debate / Opinión"
    if "/policiales/" in link or "/seguridad/" in link:
        return "Defensa / Seguridad"
    return "Sociedad"

feeds_extra = {
    "Política": [
        "http://cadena3.com/rss/PoliticayEconomia.xml",
        "https://derechadiario.com.ar/us/rss/cat/argentina"
    ],
    "Economía": [
        "http://cadena3.com/rss/PoliticayEconomia.xml"
    ],
    "Entretenimiento": [
        "http://cadena3.com/rss/Espectaculos.xml"
    ],
    "Deportes": [
        "http://cadena3.com/rss/Deportes.xml",
        "https://www.ole.com.ar/rss/ultimas-noticias/"
    ],
}

@st.cache_data(ttl=300)
def obtener_noticias(cats, desde, hasta, provincia=None):
    lista = []
    palabras_graves = [
        "urgente", "último momento", "ultimo momento",
        "alerta", "grave", "tragedia", "muerte", "accidente mortal"
    ]

    # TN
    try:
        feed = feedparser.parse(TN_FEED)
        for entry in feed.entries[:30]:
            try:
                f = datetime(*entry.published_parsed[:6]).date()
            except:
                f = datetime.now().date()

            if not (desde <= f <= hasta):
                continue

            titulo = entry.title
            if provincia and provincia.lower() not in titulo.lower():
                continue

            cat = detectar_categoria_tn(entry.link)
            if cat not in cats:
                continue

            es_grave = any(p in titulo.lower() for p in palabras_graves)
            imagen = extraer_imagen(entry)

            lista.append({
                "titulo": titulo,
                "link": entry.link,
                "medio": "TN",
                "categoria": cat,
                "fecha": f,
                "grave": es_grave,
                "imagen": imagen
            })
    except:
        pass

    # Feeds extra
    for cat in cats:
        if cat in feeds_extra:
            for url in feeds_extra[cat]:
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
                        imagen = extraer_imagen(entry)

                        lista.append({
                            "titulo": titulo,
                            "link": entry.link,
                            "medio": feed.feed.get("title", "Medio")[:40],
                            "categoria": cat,
                            "fecha": f,
                            "grave": es_grave,
                            "imagen": imagen
                        })
                except:
                    pass

    return lista

# ========== PAGINACIÓN ==========
if "pagina" not in st.session_state:
    st.session_state.pagina = 0

with st.spinner("Cargando noticias..."):
    noticias = obtener_noticias(
        categorias_activas,
        fecha_desde,
        fecha_hasta,
        provincia_seleccionada
    )

if noticias:
    noticias = sorted(noticias, key=lambda x: x["fecha"], reverse=True)

    # ===== CAMBIO: 5 noticias por página =====
    TAMANO_PAGINA = 5
    total_paginas = (len(noticias) - 1) // TAMANO_PAGINA + 1

    # Aseguramos que la página no se pase del límite
    if st.session_state.pagina >= total_paginas:
        st.session_state.pagina = total_paginas - 1
    if st.session_state.pagina < 0:
        st.session_state.pagina = 0

    inicio = st.session_state.pagina * TAMANO_PAGINA
    fin = inicio + TAMANO_PAGINA
    noticias_pagina = noticias[inicio:fin]

    # Mostrar las 5 noticias de la página actual
    for n in noticias_pagina:
        col_img, col_txt = st.columns([0.9, 5.1])

        with col_img:
            if n.get("imagen"):
                st.markdown(
                    f'''
                    <img src="{n["imagen"]}" 
                         width="120" 
                         height="80"
                         style="width:120px; height:80px; object-fit:cover; border-radius:6px; display:block;"
                         loading="lazy"
                         decoding="async"
                         onerror="this.style.display='none'">
                    ''',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '''
                    <div style="width:120px; height:80px; background:#e9ecef; 
                                border-radius:6px; display:flex; align-items:center; 
                                justify-content:center; color:#adb5bd; font-size:11px;">
                        Sin foto
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

        with col_txt:
            if n["grave"]:
                st.markdown(
                    f"""
                    <div style="background:#fff5f5; padding:8px 12px; border-left:4px solid #e03131; 
                                border-radius:4px; margin-bottom:2px;">
                        <span style="color:#e03131; font-weight:700; font-size:13px;">⚠️ ÚLTIMO MOMENTO</span><br>
                        <b style="font-size:15px; line-height:1.3;">{n['titulo']}</b><br>
                        <small style="color:#868e96;">{n['medio']} · {n['categoria']} · {n['fecha']}</small><br>
                        <a href="{n['link']}" target="_blank" style="font-size:13px;">Leer →</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="padding:2px 0 6px 0;">
                        <b style="font-size:15px; line-height:1.3;">{n['titulo']}</b><br>
                        <small style="color:#868e96;">{n['medio']} · {n['categoria']} · {n['fecha']}</small> · 
                        <a href="{n['link']}" target="_blank" style="font-size:13px;">Leer →</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ========== BOTONES DE PAGINACIÓN ==========
    st.markdown("---")
    col_ant, col_info, col_sig = st.columns([1, 2, 1])

    with col_ant:
        if st.button("⬅️ Anterior", use_container_width=True, disabled=(st.session_state.pagina == 0)):
            st.session_state.pagina -= 1
            st.rerun()

    with col_info:
        st.markdown(
            f"<div style='text-align:center; padding-top:8px;'>Página <b>{st.session_state.pagina + 1}</b> de <b>{total_paginas}</b></div>",
            unsafe_allow_html=True
        )

    with col_sig:
        if st.button("Siguiente ➡️", use_container_width=True, disabled=(st.session_state.pagina >= total_paginas - 1)):
            st.session_state.pagina += 1
            st.rerun()

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
