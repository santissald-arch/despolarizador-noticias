import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Despolarizador de Noticias Argentina", layout="wide")

# ========== LÍNEA DE TIEMPO ARRIBA ==========
st.title("🇦🇷 Despolarizador de Noticias - Argentina")

col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
with col1:
    fecha_desde = st.date_input("Desde", value=datetime.now() - timedelta(days=7))
with col2:
    fecha_hasta = st.date_input("Hasta", value=datetime.now())
with col3:
    if st.button("Ahora"):
        fecha_desde = datetime.now().date()
        fecha_hasta = datetime.now().date()
with col4:
    st.write("")  # espacio

st.markdown("---")

# ========== FILTROS IZQUIERDA ==========
st.sidebar.header("Filtros de categorías")
categorias = {
    "Política": st.sidebar.checkbox("Política", value=True),
    "Economía": st.sidebar.checkbox("Economía", value=True),
    "Defensa": st.sidebar.checkbox("Defensa"),
    "Entretenimiento": st.sidebar.checkbox("Entretenimiento"),
    "Debate": st.sidebar.checkbox("Debate"),
    "Sociedad": st.sidebar.checkbox("Sociedad"),
    "Internacional": st.sidebar.checkbox("Internacional"),
}

categorias_seleccionadas = [cat for cat, activa in categorias.items() if activa]

# ========== MAPA DE ARGENTINA ==========
st.subheader("Mapa de Argentina")

# Mapa centrado en Argentina
m = folium.Map(location=[-38.4161, -63.6167], zoom_start=4)

# Agregamos un marcador de ejemplo (después se puede mejorar)
folium.Marker(
    [-34.6037, -58.3816],
    popup="Buenos Aires",
    tooltip="Capital"
).add_to(m)

# Mostrar el mapa
st_folium(m, width=900, height=450)

# ========== NOTICIAS (ejemplos por ahora) ==========
st.subheader("Noticias filtradas")

# Datos de ejemplo (después los reemplazamos por RSS reales)
noticias_ejemplo = [
    {"titulo": "Gobierno anuncia nuevas medidas económicas", "categoria": "Economía", "medio": "Infobae", "fecha": datetime.now().date(), "link": "#"},
    {"titulo": "Debate en el Congreso sobre reforma", "categoria": "Política", "medio": "La Nación", "fecha": datetime.now().date(), "link": "#"},
    {"titulo": "Análisis de la situación de defensa nacional", "categoria": "Defensa", "medio": "Clarín", "fecha": datetime.now().date() - timedelta(days=1), "link": "#"},
    {"titulo": "Nuevo estreno en el cine argentino", "categoria": "Entretenimiento", "medio": "TN", "fecha": datetime.now().date(), "link": "#"},
    {"titulo": "Opiniones enfrentadas sobre el dólar", "categoria": "Debate", "medio": "Página/12", "fecha": datetime.now().date(), "link": "#"},
]

# Filtrar por categoría y fecha
noticias_filtradas = [
    n for n in noticias_ejemplo
    if n["categoria"] in categorias_seleccionadas
    and fecha_desde <= n["fecha"] <= fecha_hasta
]

if noticias_filtradas:
    for n in noticias_filtradas:
        st.markdown(f"*{n['titulo']}*  \n*{n['medio']}* | {n['categoria']} | {n['fecha']}  \n[Ver noticia]({n['link']})")
        st.markdown("---")
else:
    st.info("No hay noticias con los filtros seleccionados. Probá cambiar las fechas o categorías.")

# ========== ZÓCALO DE PUBLICIDAD (abajo fijo) ==========
st.markdown("""
<style>
.banner-ads {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 70px;
    background-color: #f0f2f6;
    border-top: 1px solid #ccc;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999;
    font-size: 14px;
    color: #666;
}
</style>
<div class="banner-ads">
    📢 Espacio publicitario (aquí irá Google AdSense o tu red de ads)
</div>
<div style="height: 80px;"></div>
""", unsafe_allow_html=True)
