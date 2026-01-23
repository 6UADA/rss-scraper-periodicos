# scraper_forbes.py
import re
import time
from utils import clean_article_text
import requests
from urllib.parse import urlparse
from newspaper import Article

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

WP_API_POSTS = "https://forbes.com.mx/wp-json/wp/v2/posts"
WP_API_CATS  = "https://forbes.com.mx/wp-json/wp/v2/categories"

# Fallbacks conocidos por si el WP API de categorías responde vacío para algún slug
KNOWN_SLUG_TO_CATID = {
    "internacional": 86655,
    # Añade otros si llegas a conocerlos con certeza:
    # "forbes-politica": 12345,
    # "all-access": 23456,
}

def _get(url, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", UA)
    # Algunos WAFs exigen Accept/Language razonables
    headers.setdefault("Accept", "text/html,application/json;q=0.9,*/*;q=0.8")
    headers.setdefault("Accept-Language", "es-MX,es;q=0.9,en;q=0.8")
    return requests.get(url, headers=headers, timeout=kwargs.pop("timeout", 25), **kwargs)

def _slug_from_section_url(url: str) -> str | None:
    """
    Toma la URL de sección y devuelve el slug más probable de categoría.
    Ejemplos:
      https://forbes.com.mx/internacional/         -> internacional
      https://forbes.com.mx/forbes-politica/       -> forbes-politica
      https://forbes.com.mx/forbes-life/all-access/-> all-access
    """
    path = urlparse(url).path.strip("/")
    if not path:
        return None
    parts = [p for p in path.split("/") if p]
    # Usamos el último segmento (si es 'page' o numérico, tomamos el anterior)
    last = parts[-1].lower()
    if last in ("page",) or re.fullmatch(r"\d+", last):
        last = parts[-2].lower() if len(parts) > 1 else None
    return last

def _cat_id_from_slug(slug: str) -> int | None:
    """
    Consulta el endpoint de categorías por slug exacto.
    """
    # Fallback conocido primero (evita un viaje si ya lo sabemos)
    if slug in KNOWN_SLUG_TO_CATID:
        return KNOWN_SLUG_TO_CATID[slug]

    try:
        r = _get(WP_API_CATS, params={"slug": slug, "per_page": 1})
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            return int(data[0]["id"])
    except requests.HTTPError as he:
        code = he.response.status_code if he.response is not None else "?"
        print(f"[Forbes] HTTP {code} al consultar categorías para slug='{slug}'.")
    except Exception as e:
        print(f"[Forbes] Error resolviendo categoría por slug='{slug}': {e}")
    return None

def _posts_from_category(cat_id: int, per_page: int = 20, max_pages: int = 1) -> list[dict]:
    """
    Recupera posts por categoría desde WP REST, con _embed para autores y media.
    Soporta paginación simple (max_pages).
    """
    items = []
    page = 1
    while page <= max_pages and len(items) < per_page:
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
                break  # no hay más páginas
            r.raise_for_status()
            data = r.json()
        except requests.HTTPError as he:
            code = he.response.status_code if he.response is not None else "?"
            try:
                msg = he.response.json().get("message", str(he))
            except Exception:
                msg = str(he)
            print(f"[Forbes] HTTP {code} al pedir posts (cat_id={cat_id}, page={page}): {msg}")
            break
        except Exception as e:
            print(f"[Forbes] Error inesperado al pedir posts (cat_id={cat_id}, page={page}): {e}")
            break

        if not isinstance(data, list) or not data:
            break

        for p in data:
            link = p.get("link")
            title = (p.get("title") or {}).get("rendered")
            # Autores desde _embedded
            authors = []
            for a in p.get("_embedded", {}).get("author", []) or []:
                name = a.get("name")
                if name:
                    authors.append(name)
            # Imagen destacada (si existe)
            top_img = None
            media = p.get("_embedded", {}).get("wp:featuredmedia", [])
            if media and isinstance(media, list) and media[0].get("source_url"):
                top_img = media[0]["source_url"]

            # Descargar cuerpo con newspaper3k para texto limpio
            texto = ""
            titulo = title or ""
            # autores = authors # Removed
            imagen = top_img
            try:
                if link:
                    art = Article(link)
                    art.download()
                    art.parse()
                    texto = art.text or ""
                    if not titulo:
                        titulo = art.title or ""
                    # if not autores: # Removed
                    #     autores = art.authors or []
                    if not imagen:
                        imagen = art.top_image or None
            except Exception as e:
                print(f"[Forbes] Aviso: fallo al parsear artículo: {link} ({e})")

            # Limpieza centralizada
            cleaned_text = clean_article_text(texto)

            items.append({
                "url": link,
                "titulo": titulo,
                "texto": cleaned_text,
                "imagen_url": imagen
            })

            time.sleep(0.35)  # throttle suave

        page += 1

    # Recorta a per_page por si se juntó de varias páginas
    return items[:per_page]

def scrape_forbes(url: str) -> list[dict]:
    """
    Recibe la URL de la sección (desde main) y devuelve artículos.
    Evita pedir el HTML de la sección (para esquivar 403/503) y resuelve la categoría por slug.
    """
    print(f"[Forbes] Procesando sección: {url}")
    slug = _slug_from_section_url(url)
    if not slug:
        print("[Forbes] No se pudo deducir un slug de categoría desde la URL. Devolviendo 0 artículos.")
        return []

    cat_id = _cat_id_from_slug(slug)
    if not cat_id:
        print(f"[Forbes] No fue posible determinar el ID de categoría para slug='{slug}'. Devolviendo 0 artículos.")
        return []

    print(f"[Forbes] Categoría '{slug}' -> ID {cat_id}. Consultando posts…")
    items = _posts_from_category(cat_id, per_page=20, max_pages=2)
    print(f"[Forbes] Se obtuvieron {len(items)} artículos.")
    return items
