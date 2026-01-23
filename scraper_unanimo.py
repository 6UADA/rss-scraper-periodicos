# scraper_unanimo.py
import time
import requests
from urllib.parse import urlparse
from newspaper import Article
from bs4 import BeautifulSoup
from utils import clean_article_text

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

BASE = "https://unanimodeportes.com"
WP_API_POSTS = f"{BASE}/wp-json/wp/v2/posts"
WP_API_CATS  = f"{BASE}/wp-json/wp/v2/categories"

def _get(url, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", UA)
    headers.setdefault("Accept", "application/json,text/html;q=0.9,*/*;q=0.8")
    headers.setdefault("Accept-Language", "es-ES,es;q=0.9,en;q=0.8")
    return requests.get(url, headers=headers, timeout=kwargs.pop("timeout", 25), **kwargs)

def _cat_id_from_slug(slug: str) -> int | None:
    """Intenta resolver el ID exacto por slug y, si no, busca por 'search'."""
    # 1) slug exacto
    try:
        r = _get(WP_API_CATS, params={"slug": slug, "per_page": 1})
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            return int(data[0]["id"])
    except Exception:
        pass
    # 2) búsqueda amplia y elegir la que tenga slug igual
    try:
        r = _get(WP_API_CATS, params={"search": slug, "per_page": 10})
        r.raise_for_status()
        for c in r.json():
            if c.get("slug") == slug:
                return int(c["id"])
        # si no hay slug exacto, devuelve la primera coincidencia
        data = r.json()
        if isinstance(data, list) and data:
            return int(data[0]["id"])
    except Exception:
        pass
    return None

def _posts_from_category(cat_id: int, per_page: int = 20, pages: int = 1) -> list[dict]:
    items = []
    for page in range(1, pages + 1):
        try:
            r = _get(WP_API_POSTS, params={
                "categories": cat_id,
                "per_page": min(per_page, 50),
                "page": page,
                "_embed": 1,
                "orderby": "date",
                "order": "desc",
            })
            if r.status_code == 400 and "rest_post_invalid_page_number" in r.text:
                break
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[Unanimo] Error posts cat_id={cat_id} page={page}: {e}")
            break

        if not data:
            break

        for p in data:
            link = p.get("link")
            title = (p.get("title") or {}).get("rendered") or ""
            # autores via _embed
            authors = []
            for a in p.get("_embedded", {}).get("author", []) or []:
                name = a.get("name")
                if name:
                    authors.append(name)
            # imagen destacada
            top_img = None
            media = p.get("_embedded", {}).get("wp:featuredmedia", [])
            if media and isinstance(media, list) and media[0].get("source_url"):
                top_img = media[0]["source_url"]

            # cuerpo con newspaper3k
            texto, titulo, autores, imagen = "", title, authors, top_img
            try:
                if link:
                    art = Article(link, language="es")
                    art.download(); art.parse()
                    texto = art.text or ""
                    if not titulo:
                        titulo = art.title or ""
                    if not autores:
                        autores = art.authors or []
                    if not imagen:
                        imagen = art.top_image or None
            except Exception as e:
                print(f"[Unanimo] Aviso parseando: {link} ({e})")

            # Limpieza centralizada
            cleaned_text = clean_article_text(texto)

            items.append({
                "url": link,
                "titulo": titulo,
                "texto": cleaned_text,
                "imagen_url": imagen
            })
            time.sleep(0.35)

        # si ya llenamos per_page, paramos
        if len(items) >= per_page:
            break

    return items[:per_page]

def _posts_from_rss(category_url: str, limit: int = 20) -> list[dict]:
    """Fallback por RSS: /feed/ de la categoría."""
    feed_url = category_url.rstrip("/") + "/feed/"
    try:
        r = _get(feed_url)
        r.raise_for_status()
    except Exception as e:
        print(f"[Unanimo] RSS no disponible: {e}")
        return []

    soup = BeautifulSoup(r.text, "xml")
    items = []
    for it in soup.find_all("item")[:limit]:
        link = it.find("link").get_text(strip=True) if it.find("link") else None
        if not link:
            continue
        titulo = it.find("title").get_text(strip=True) if it.find("title") else ""
        autores = []
        author_tag = it.find("dc:creator")
        if author_tag:
            autores = [author_tag.get_text(strip=True)]
        # newspaper para texto/imagen
        texto, imagen = "", None
        try:
            art = Article(link, language="es")
            art.download(); art.parse()
            texto = art.text or ""
            if not titulo:
                titulo = art.title or ""
            if not autores:
                autores = art.authors or []
            imagen = art.top_image or None
        except Exception as e:
            print(f"[Unanimo][RSS] Aviso parseando: {link} ({e})")

        # Limpieza centralizada
        cleaned_text = clean_article_text(texto)

        items.append({
            "url": link,
            "titulo": titulo,
            "texto": cleaned_text,
            "imagen_url": imagen
        })
        time.sleep(0.35)
    return items

def scrape_unanimo(url: str) -> list[dict]:
    """
    Recibe la URL de categoría (p.ej. https://unanimodeportes.com/deportes/futbol/)
    1) Resuelve cat_id por WP REST y trae posts.
    2) Si falla, usa RSS de la categoría.
    """
    print(f"[Unanimo] Procesando sección: {url}")
    # Determinar slug de la categoría final en el path (e.g., 'futbol')
    path_parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
    slug = path_parts[-1].lower() if path_parts else "futbol"

    cat_id = _cat_id_from_slug(slug)
    if cat_id:
        print(f"[Unanimo] Categoría '{slug}' -> ID {cat_id}. Consultando WP REST API…")
        items = _posts_from_category(cat_id, per_page=20, pages=2)
        if items:
            print(f"[Unanimo] {len(items)} artículos desde WP REST API.")
            return items
        else:
            print("[Unanimo] API devolvió 0 artículos. Intentaré RSS…")
    else:
        print("[Unanimo] No se pudo resolver la categoría por API. Intentaré RSS…")

    # Fallback RSS
    items = _posts_from_rss(url, limit=20)
    print(f"[Unanimo] {len(items)} artículos desde RSS.")
    return items
