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
texto_banner
