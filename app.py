@st.cache_data(ttl=180)
def obtener_tapa_infobae():
    """Trae la noticia principal de la edición Argentina de Infobae.

    La home https://www.infobae.com/ redirige por geolocalización del servidor
    (América, México, etc.), así que no se usa. Se prioriza el RSS de Política
    (contenido AR) y, como respaldo, el RSS general filtrado a secciones locales.
    El título se toma del RSS (a veces difiere del H1/og:title de la nota).
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; NoticiasApp/1.0)"}
    _EXCLUIDAS = [
        "/mexico/", "/colombia/", "/chile/", "/peru/", "/venezuela/",
        "/america/", "/estados-unidos/", "/espana/", "/centroamerica/",
        "/teleshow/", "/tendencias/",
    ]

    def _es_valida(url: str) -> bool:
        if "infobae.com" not in url or "/arc/outboundfeeds" in url:
            return False
        return not any(s in url for s in _EXCLUIDAS)

    def _imagen_de_entry(entry) -> str | None:
        img = extraer_imagen(entry)
        if img:
            return img
        # media:content del RSS de Arc
        if hasattr(entry, "media_content") and entry.media_content:
            for m in entry.media_content:
                u = m.get("url")
                if u:
                    return u
        return None

    def _desde_feed(feed_url: str):
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:12]:
                link = (entry.get("link") or "").strip()
                if not _es_valida(link):
                    continue
                titulo = (entry.get("title") or "").strip()
                if len(titulo) < 20:
                    continue
                return {
                    "titulo": titulo,
                    "link": link,
                    "imagen": _imagen_de_entry(entry),
                }
        except Exception:
            return None
        return None

    # 1) Política = hard news Argentina (lo más cercano a la tapa local)
    tapa = _desde_feed(
        "https://www.infobae.com/arc/outboundfeeds/rss/category/politica/"
    )

    # 2) Respaldo: feed general, solo secciones AR
    if not tapa:
        tapa = _desde_feed("https://www.infobae.com/arc/outboundfeeds/rss/")

    # 3) Completar imagen si el RSS no la trajo
    if tapa and not tapa.get("imagen"):
        try:
            r = requests.get(tapa["link"], headers=headers, timeout=8)
            m = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
            if m:
                tapa["imagen"] = m.group(1)
        except Exception:
            pass

    return tapa
