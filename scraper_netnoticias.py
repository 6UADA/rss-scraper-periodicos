import requests
from bs4 import BeautifulSoup
from newspaper import Article
import time
from utils import clean_article_text

def scrape_netnoticias(url):
    """
    Rastrea Netnoticias usando BeautifulSoup para extraer artículos.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL de Netnoticias: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Enlaces principales del carrusel y de las secciones
    article_links = []
    
    # Contenedor del artículo principal
    main_article = soup.find('a', href=True, class_='text-headline-title')
    if main_article:
        article_links.append(main_article['href'])

    # Contenedores de las secciones de noticias
    news_blocks = soup.select('div.grid.grid-cols-4.gap-6.mb-6 a')
    for block in news_blocks:
        if 'href' in block.attrs:
            article_links.append(block['href'])

    scraped_articles = []
    print(f"Se encontraron {len(article_links)} enlaces en Netnoticias.")

    for link in set(article_links):
        try:
            if not link.startswith('http'):
                link = requests.compat.urljoin(url, link)
            
            article = Article(link)
            article.download()
            article.parse()
            
            # Limpieza centralizada
            cleaned_text = clean_article_text(article.text)

            scraped_articles.append({
                "url": link,
                "titulo": article.title,
                "texto": cleaned_text,
                "imagen_url": article.top_image
            })
            
            print(f"Artículo de Netnoticias extraído: {article.title}")
            time.sleep(1)
            
        except Exception as e:
            print(f"Error al procesar el artículo de Netnoticias {link}: {e}")
    
    return scraped_articles