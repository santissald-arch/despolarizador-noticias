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

h1, h2, h3, .stTitle {
    font-family: 'Playfair Display', serif !important;
    color: #f5f0e6 !important;
    letter-spacing: -0.5px;
}

.stApp {
    background: linear-gradient(180deg, #0c0c0c 0%, #141414 100%);
}

/* Sidebar premium */
section[data-testid="stSidebar"] {
    background: #111111;
    border-right: 1px solid #2a2a2a;
}

/* Cards elegantes */
.premium-card {
    background: linear-gradient(145deg, #1a1a1a, #151515);
    border: 1px solid #2c2c2c;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    transition: all 0.3s ease;
}

.premium-card:hover {
    border-color: #c9a84c;
    box-shadow: 0 12px 40px rgba(201, 168, 76, 0.15);
}

/* Botones elegantes */
.stButton > button {
    background: linear-gradient(135deg, #c9a84c, #a88b3a) !important;
    color: #0c0c0c !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px;
    transition: all 0.25s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(201, 168, 76, 0.35);
}

/* Links */
a {
    color: #c9a84c !important;
    text-decoration: none !important;
}
a:hover {
    color: #e0c06e !important;
}

/* Separadores */
hr {
    border-color: #2a2a2a !important;
}

/* Marquee premium */
.marquee {
    background: #0a0a0a !important;
    border-bottom: 1px solid #2a2a2a;
    color: #c9a84c !important;
}
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

# ========== DIARIOS PROVINCIALES (2 por provincia) ==========
DIARIOS_PROVINCIALES = {
    "Buenos Aires": [
        "https://www.eldia.com/rss",
        "https://www.lanueva.com/rss"
    ],
    "Ciudad Autónoma de Buenos Aires": [
        "https://www.clarin.com/rss/lo-ultimo/",
        "https://www.lanacion.com.ar/arc/outboundfeeds/rss/?outputType=xml"
    ],
    "Catamarca": [
        "https://www.elancasti.com.ar/rss",
        "https://www.catamarcactual.com.ar/feed"
    ],
    "Chaco": [
        "https://www.diarionorte.com/rss",
        "https://www.primeraedicionweb.com.ar/feed"
    ],
    "Chubut": [
        "https://www.elchubut.com.ar/rss",
        "https://www.diariojornada.com.ar/rss"
    ],
    "Córdoba": [
        "https://www.lavoz.com.ar/rss",
        "https://www.lavozdelinterior.com.ar/rss"
    ],
    "Corrientes": [
        "https://www.ellitoral.com.ar/rss",
        "https://www.diarioepoca.com/rss"
    ],
    "Entre Ríos": [
        "https://www.unoentrerios.com.ar/rss",
        "https://www.elheraldo.com.ar/rss"
    ],
    "Formosa": [
        "https://www.diariolaformosa.com/rss",
        "https://www.formosa.gob.ar/rss"
    ],
    "Jujuy": [
        "https://www.eltribuno.com/jujuy/rss",
        "https://www.jujuyalmomento.com/feed"
    ],
    "La Pampa": [
        "https://www.laarena.com.ar/rss",
        "https://www.eldiariodelapampa.com.ar/rss"
    ],
    "La Rioja": [
        "https://www.elindependiente.com.ar/rss",
        "https://www.riojavirtual.com.ar/feed"
    ],
    "Mendoza": [
        "https://www.losandes.com.ar/rss",
        "https://www.diariouno.com.ar/rss"
    ],
    "Misiones": [
        "https://www.misionesonline.net/feed",
        "https://www.elterritorio.com.ar/rss/ahora/"
    ],
    "Neuquén": [
        "https://www.lmneuquen.com/rss",
        "https://www.rionegro.com.ar/feed/"
    ],
    "Río Negro": [
        "https://www.rionegro.com.ar/feed/",
        "https://www.bariloche2000.com/rss"
    ],
    "Salta": [
        "https://www.eltribuno.com/salta/rss",
        "https://www.saltalibre.com/feed"
    ],
    "San Juan": [
        "https://www.diariodecuyo.com.ar/rss",
        "https://www.tiemposanjuan.com/rss"
    ],
    "San Luis": [
        "https://www.eldiariodelarepublica.com/rss",
        "https://www.sanluis.gov.ar/rss"
    ],
    "Santa Cruz": [
        "https://www.laopinionaustral.com.ar/rss",
        "https://www.tiemposur.com.ar/rss"
    ],
    "Santa Fe": [
        "https://www.lacapital.com.ar/rss",
        "https://www.ellitoral.com/rss"
    ],
    "Santiago del Estero": [
        "https://www.elliberal.com.ar/rss",
        "https://www.diariopanorama.com/rss"
    ],
    "Tierra del Fuego": [
        "https://www.surenio.com.ar/rss",
        "https://www.tierradelfuego.gov.ar/rss"
    ],
    "Tucumán": [
        "https://www.lagaceta.com.ar/rss",
        "https://feeds.feedburner.com/LaGaceta"
    ],
}

# ========== NOTICIA DEL DÍA + TN VIVO ==========
st.markdown("---")
st.subheader("Destacados")

def extraer_imagen(entry):
    if hasattr(entry, "media_content") and entry.media_content:
        for m in entry.media_content:
            url = m.get("url")
            if url and (m.get("type", "").startswith("image") or url.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))):
                return url
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            url = enc.get("href") or enc.get("url")
            if url and url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                return url
    content = entry.get("summary", "") or (entry.get("content")[0].get("value", "") if entry.get("content") else "")
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
    return match.group(1) if match else None

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

    # 1. Fuentes nacionales (TN + extras)
    fuentes = [TN_FEED]
    for cat in cats:
        if cat in feeds_extra:
            fuentes.extend(feeds_extra[cat])

    # 2. Si hay provincia seleccionada → agregar sus 2 diarios principales
    if provincia and provincia in DIARIOS_PROVINCIALES:
        fuentes.extend(DIARIOS_PROVINCIALES[provincia])

    for url in set(fuentes):  # sin duplicados
        try:
            feed = feedparser.parse(url)
            medio_nombre = feed.feed.get("title", "Medio")[:40]
            for entry in feed.entries[:15]:
                try:
                    f = datetime(*entry.published_parsed[:6]).date()
                except:
                    f = datetime.now().date()

                if not (desde <= f <= hasta):
                    continue

                titulo = entry.title

                # Filtro de provincia
                if provincia and provincia.lower() not in titulo.lower() and provincia not in DIARIOS_PROVINCIALES.get(provincia, []):
                    # Si es un diario provincial, lo dejamos pasar
                    if url not in DIARIOS_PROVINCIALES.get(provincia, []):
                        continue

                # Categoría (solo para TN, los provinciales van como Sociedad por defecto)
                if "tn.com.ar" in url:
                    cat = detectar_categoria_tn(entry.link)
                else:
                    cat = "Sociedad"

                if cat not in cats and "tn.com.ar" in url:
                    continue

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

# ========== PAGINACIÓN ==========
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

    for n in noticias_pagina:
        col_img, col_txt = st.columns([1, 5])
        with col_img:
            if n.get("imagen"):
                st.markdown(f'''
                    <img src="{n["imagen"]}" style="width:110px; height:75px; object-fit:cover; border-radius:8px;" 
                         onerror="this.style.display='none'">
                ''', unsafe_allow_html=True)
            else:
                st.markdown('''
                    <div style="width:110px; height:75px; background:#1f1f1f; border-radius:8px; 
                                display:flex; align-items:center; justify-content:center; color:#555; font-size:11px;">
                        Sin imagen
                    </div>
                ''', unsafe_allow_html=True)

        with col_txt:
            if n["grave"]:
                st.markdown(f"""
                <div style="border-left:3px solid #c9a84c; padding-left:14px; margin-bottom:8px;">
                    <span style="color:#c9a84c; font-size:11px; font-weight:600;">ÚLTIMO MOMENTO</span><br>
                    <b style="font-size:16px; color:#f5f0e6;">{n['titulo']}</b><br>
                    <small style="color:#888;">{n['medio']} · {n['categoria']} · {n['fecha']}</small> · 
                    <a href="{n['link']}" target="_blank">Leer</a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="padding:4px 0 10px 0;">
                    <b style="font-size:16px; color:#f5f0e6;">{n['titulo']}</b><br>
                    <small style="color:#888;">{n['medio']} · {n['categoria']} · {n['fecha']}</small> · 
                    <a href="{n['link']}" target="_blank">Leer</a>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    col_ant, col_info, col_sig = st.columns([1, 2, 1])
    with col_ant:
        if st.button("← Anterior", use_container_width=True, disabled=(st.session_state.pagina == 0)):
            st.session_state.pagina -= 1
            st.rerun()
    with col_info:
        st.markdown(f"<div style='text-align:center; padding-top:8px; color:#aaa;'>Página <b>{st.session_state.pagina + 1}</b> de <b>{total_paginas}</b></div>", unsafe_allow_html=True)
    with col_sig:
        if st.button("Siguiente →", use_container_width=True, disabled=(st.session_state.pagina >= total_paginas - 1)):
            st.session_state.pagina += 1
            st.rerun()
else:
    st.info("No se encontraron noticias con esos filtros. Probá ampliar las fechas o seleccionar otra provincia.")

# ========== FOOTER ==========
st.markdown("""
<div style="height:40px;"></div>
<div style="text-align:center; padding:20px 0; border-top:1px solid #2a2a2a; color:#666; font-size:12px;">
    Noticias de Argentina · Diseño premium · Buenos Aires
</div>
""", unsafe_allow_html=True)
