# scraper_noventagrados.py
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import time
from utils import clean_article_text

def scrape_noventagrados(url):
    """
    Rastrea Noventa Grados usando BeautifulSoup para extraer artículos.
    """
    # Código de la función scrape_noventagrados...
    # ...
    # ...
   
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL de Noventa Grados: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    article_containers = soup.find_all('div', class_='nota_con_imagen')
    article_links = [container.find('a', class_='nota_con_imagen_link')['href'] for container in article_containers if container.find('a', class_='nota_con_imagen_link')]
    
    scraped_articles = []
    print(f"Se encontraron {len(article_links)} enlaces en Noventa Grados.")

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
            
            print(f"Artículo de Noventa Grados extraído: {article.title}")
            time.sleep(1)
            
        except Exception as e:
            print(f"Error al procesar el artículo de Noventa Grados {link}: {e}")
    
    return scraped_articles