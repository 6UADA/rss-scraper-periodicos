# scraper_excelsior.py
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import time
from utils import clean_article_text

def scrape_excelsior(url):
    """
    Rastrea Excélsior usando BeautifulSoup para extraer artículos.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL de Excelsior: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Determinamos el slug de la sección de la URL para filtrar
    # Ejemplo: /global, /nacional, /funcion o /internacional
    section_slug = url.split('.mx/')[-1].split('/')[0]
    
    # Mapeo de slugs alternativos que usa Excelsior internamente
    slug_mappings = {
        'global': 'internacional',
        'funcion': 'espectaculos'
    }
    alt_slug = slug_mappings.get(section_slug)
    
    # Buscamos los enlaces de forma más segmentada para evitar menús
    article_links = []
    
    # Excluir navegación, cabecera y pie de página para no traer secciones cruzadas del menú
    for tag in soup(['nav', 'header', 'footer']):
        tag.decompose()

    # Buscamos todos los links que pertenezcan a la sección actual
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Debe contener el slug de la sección O el alternativo
        is_correct_section = f"/{section_slug}/" in href or (alt_slug and f"/{alt_slug}/" in href)
        
        # Filtramos links cortos que suelen ser de carpetas/secciones, no de notas
        # Una nota suele ser larga y tener varias palabras separadas por guiones
        passed_length = len(href.split('/')) > 2 and len(href) > len(section_slug) + 5
        
        if is_correct_section and passed_length:
            article_links.append(href)
        elif "/nacional/" in href or "/global/" in href:
            # Debug: ¿Por qué estamos saltando links que parecen notas?
            # print(f"DEBUG: Saltado {href} (CorrectSec: {is_correct_section}, PassedLen: {passed_length})")
            pass
    
    scraped_articles = []
    # Eliminar duplicados manteniendo orden
    seen_links = set()
    unique_links = []
    for l in article_links:
        if l not in seen_links:
            unique_links.append(l)
            seen_links.add(l)

    print(f"Se encontraron {len(unique_links)} enlaces únicos en la sección {section_slug} de Excelsior.")

    for link in set(article_links):
        try:
            if not link.startswith('http'):
                link = requests.compat.urljoin(url, link)
            
            article = Article(link)
            article.download()
            article.parse()
            
            # Crear soup específico para esta nota (CRUCIAL: No reutilizar el soup de la sección)
            article_soup = BeautifulSoup(article.html, 'html.parser')
            
            # Limpieza centralizada
            cleaned_text = clean_article_text(article.text)
            
            # Filtro específico para Excelsior: solo notas del año actual (2026+)
            # para evitar traer contenido "Evergreen" del 2025 que sigue en su portada.
            from utils import is_from_current_year
            if not is_from_current_year(article.publish_date):
                print(f"Saltando nota antigua de Excelsior: {article.title} ({article.publish_date})")
                continue

            # Validación de título: Evitar que el autor sea el título
            titulo = article.title
            if titulo and titulo.startswith('Por: '):
                 # En Excelsior, el título real suele estar en meta og:title.
                 pass

            # Mejora de extracción de imagen: Scoped search y alta resolución
            imagen_url = None
            
            # Identificamos el contenedor principal de la nota (c-detail)
            # Y específicamente el área de multimedia (c-detail__media) para la foto principal
            detail_container = article_soup.find('div', class_='c-detail') or article_soup.find('article')
            media_area = article_soup.find('div', class_='c-detail__media')
            
            # El search_area es donde buscaremos si no hay media_area específica
            search_area = media_area if media_area else (detail_container if detail_container else article_soup)

            # 1. Buscamos en tags <source> (responsive images) DENTRO del área multimedia
            sources = search_area.find_all('source', attrs={'srcset': True})
            for src in sources:
                srcset = src['srcset']
                if 'main_image_813_542' in srcset or src.get('width') == '813':
                    imagen_url = srcset
                    break
            
            # 2. Si no, cualquier 'main_image' DENTRO del área multimedia
            if not imagen_url:
                for src in sources:
                    if 'main_image' in src['srcset']:
                        imagen_url = src['srcset']
                        break
            
            # 3. Si no hay source específica en la nota, intentamos og:image (metadata oficial)
            if not imagen_url:
                og_image = article_soup.find('meta', attrs={'property': 'og:image'})
                if og_image and og_image.get('content'):
                    imagen_url = og_image['content']
            
            # 4. Fallback: primera imagen real de la nota (evitando logos y basura del sidebar)
            generics = ['logo', 'header', 'default_social', 'og_thumbnail', 'placeholder', 'fallback']
            is_generic = any(g in str(imagen_url).lower() for g in generics) if imagen_url else True
            
            if is_generic or not imagen_url:
                # Buscamos primero en el área multimedia, luego en el resto de la nota
                for area in [media_area, detail_container]:
                    if not area: continue
                    for img in area.find_all('img'):
                        src = img.get('src') or img.get('data-src') or ''
                        if ('/uploads/' in src or '/files/' in src) and not any(g in src.lower() for g in generics):
                            imagen_url = src
                            break
                    if imagen_url: break
            
            # Asegurar URL absoluta
            if imagen_url and not imagen_url.startswith('http'):
                imagen_url = requests.compat.urljoin(link, imagen_url)

            scraped_articles.append({
                "url": link,
                "titulo": titulo,
                "texto": cleaned_text,
                "imagen_url": imagen_url
            })
            
            print(f"   [Excelsior] {titulo[:60]}... (Año: {article.publish_date.year if article.publish_date else '?'})")
            time.sleep(1)
            
        except Exception as e:
            print(f"   [Error Excelsior] {link}: {e}")
    
    return scraped_articles