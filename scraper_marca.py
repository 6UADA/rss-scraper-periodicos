# scraper_marca.py
import time
from utils import clean_article_text
import re
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from newspaper import Article

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def _get(url, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", UA)
    headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    headers.setdefault("Accept-Language", "es-MX,es;q=0.9,en;q=0.8")
    return requests.get(url, headers=headers, timeout=kwargs.pop("timeout", 25), **kwargs)

def _is_article_url(href: str) -> bool:
    if not href or not href.startswith("http"):
        return False
    # descartar ruido común
    bad = (
        "javascript:", "#", "/rss", "/podcast", "/video", "/videos",
        "/marca_tv", "/directo", "/clasificacion", "/resultados",
        "/album", "/galeria", "/suscripcion", "/privacidad", "/contacto",
        "/cookies", "/terms", "/aviso", "/newsletter"
    )
    if any(b in href for b in bad):
        return False

    # Marca MX suele publicar URLs con /mx/ o artículos con fecha en la ruta
    path = urlparse(href).path.lower()
    return ("/mx/" in path) or re.search(r"/\d{4}/\d{2}/\d{2}/", path) is not None

def _collect_links(base_url: str, soup: BeautifulSoup) -> list[str]:
    links = []

    # Selectores útiles del layout de Marca (portadas y listados)
    selectors = [
        # enlaces dentro de artículos/tarjetas
        "article a[href]",
        ".ue-c-cover-content__link[href]",
        ".ue-c-article__link[href]",
        ".mod-portadilla a[href]",
        ".ue-c-card__header a[href]",
        ".ue-c-card__link[href]",
        ".ue-c-article__header a[href]",
        # fallback amplio
        "a[href]"
    ]

    seen = set()
    for sel in selectors:
        for a in soup.select(sel):
            href = a.get("href")
            if not href:
                continue
            if not href.startswith("http"):
                href = urljoin(base_url, href)
            href = href.split("?")[0]  # limpia querystrings
            if href in seen:
                continue
            if _is_article_url(href):
                seen.add(href)
                links.append(href)

    return links

def _fallback_parse_with_bs(url: str, html: str) -> tuple[str, list[str], str, str | None]:
    """
    Fallback mínimo si newspaper falla: (titulo, autores, texto, imagen)
    """
    soup = BeautifulSoup(html, "html.parser")
    # Título
    title = None
    ogt = soup.find("meta", property="og:title")
    if ogt and ogt.get("content"):
        title = ogt["content"].strip()
    if not title and soup.title:
        title = soup.title.get_text(strip=True)

    # Imagen
    ogi = soup.find("meta", property="og:image")
    image = ogi.get("content").strip() if ogi and ogi.get("content") else None

    # Autores (mejor esfuerzo)
    authors = []
    for meta_name in ("author", "article:author"):
        m = soup.find("meta", attrs={"name": meta_name}) or soup.find("meta", property=meta_name)
        if m and m.get("content"):
            authors.append(m["content"].strip())
    authors = list(dict.fromkeys(a for a in authors if a))

    # Texto simple (párrafos dentro del contenido principal; mejor esfuerzo)
    # Muchos artículos usan bloques con 'ue-l-article__body' o similar.
    text = ""
    body = soup.select_one(".ue-l-article__body, .ue-c-article__body, article")
    if body:
        ps = [p.get_text(" ", strip=True) for p in body.select("p") if p.get_text(strip=True)]
        text = "\n".join(ps)

    return title or "", authors, text, image

def scrape_marca(url: str) -> list[dict]:
    """
    Recibe una URL de sección o portada de Marca (p. ej. https://www.marca.com/mx/)
    y devuelve una lista de artículos con: url, titulo, autores, texto, imagen_url.
    """
    print(f"[Marca] Raspando sección: {url}")
    try:
        resp = _get(url)
        resp.raise_for_status()
    except requests.HTTPError as he:
        code = he.response.status_code if he.response is not None else "?"
        print(f"[Marca] HTTP {code} al cargar la portada/sección: {url}")
        return []
    except Exception as e:
        print(f"[Marca] Error al cargar la portada/sección: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = _collect_links(url, soup)

    # Deduplicado manteniendo orden
    seen = set()
    article_links = [h for h in links if not (h in seen or seen.add(h))]

    print(f"[Marca] Se encontraron {len(article_links)} enlaces candidatos.")

    items = []
    for link in article_links:
        try:
            art = Article(link, language="es")
            art.download()
            art.parse()
            titulo = art.title or ""
            autores = art.authors or []
            texto = art.text or ""
            imagen = art.top_image or None

            # Fallback si newspaper devuelve poco
            if (not titulo or len(texto) < 200) and art.html:
                t2, a2, txt2, img2 = _fallback_parse_with_bs(link, art.html)
                titulo = titulo or t2
                # if not autores and a2: # Removed
                #     autores = a2
                if len(texto) < 200 and txt2:
                    texto = txt2
                if not imagen and img2:
                    imagen = img2

            # Limpieza centralizada
            cleaned_text = clean_article_text(texto)

            items.append({
                "url": link,
                "titulo": titulo,
                "texto": cleaned_text,
                "imagen_url": imagen
            })
            print(f"[Marca] OK: {titulo[:70]}{'...' if len(titulo) > 70 else ''}")
            time.sleep(0.35)  # throttle suave
        except Exception as e:
            print(f"[Marca] Aviso: fallo al procesar {link} ({e})")

    return items
