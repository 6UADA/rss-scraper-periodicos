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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL de Excelsior: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Buscamos los contenedores de artículos en las diferentes listas de la página
    article_links = []
    
    # Lista principal de noticias (lista-big)
    for container in soup.find_all('div', class_='listado-big'):
        links = container.find_all('a', href=True)
        for link in links:
            article_links.append(link['href'])

    # Contenedores de artículos pequeños (list-media-custom)
    for container in soup.find_all('ul', class_='list-media-custom'):
        links = container.find_all('a', href=True)
        for link in links:
            article_links.append(link['href'])
    
    scraped_articles = []
    print(f"Se encontraron {len(article_links)} enlaces en Excelsior.")

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
            
            print(f"Artículo de Excelsior extraído: {article.title}")
            time.sleep(1)
            
        except Exception as e:
            print(f"Error al procesar el artículo de Excelsior {link}: {e}")
    
    return scraped_articles