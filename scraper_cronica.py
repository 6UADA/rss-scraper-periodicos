# scraper_cronica.py
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from utils import clean_article_text

def scrape_cronica(url):
    """
    Rastrea La Crónica usando Selenium para manejar la carga dinámica de la página
    y evitar bloqueos.
    """
    # Usamos Selenium para abrir el navegador en modo "headless" (sin ventana visible)
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=options)
    
    scraped_articles = []

    try:
        driver.get(url)

        # Esperamos a que el elemento que contiene las noticias se cargue
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "lc-top-table-list"))
        )
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Selectores específicos para La Crónica
        article_links = []
        
        for tag in soup.find_all(class_='extra-large-container-la-cronica'):
            if tag.find('a', class_='extra-large-title'):
                article_links.append(tag.find('a', class_='extra-large-title')['href'])

        for tag in soup.find_all(class_='medium-container-la-cronica'):
            if tag.find('a', class_='medium-title'):
                article_links.append(tag.find('a', class_='medium-title')['href'])

        for tag in soup.find_all(class_='small-container-la-cronica'):
            if tag.find('a', class_='small-title'):
                article_links.append(tag.find('a', class_='small-title')['href'])
        
        print(f"Se encontraron {len(article_links)} enlaces en La Crónica.")

        for link in set(article_links):
            try:
                if not link.startswith('http'):
                    link = requests.compat.urljoin(url, link)
                
                article = Article(link)
                article.download()
                article.parse()
                
                # Limpieza centralizada
                cleaned_text = clean_article_text(article.text)
                clean_text = cleaned_text.split('\n') # Mantener compatibilidad si se usa como lista abajo, o ajustar uso.
                # Revisando uso: "texto": "\n".join(clean_text) -> "texto": cleaned_text

                scraped_articles.append({
                    "url": link,
                    "titulo": article.title,
                    "texto": cleaned_text,
                    "imagen_url": article.top_image
                })
                
                print(f"Artículo de Cronica extraído: {article.title}")
                time.sleep(3) # Pausa para evitar bloqueos
                
            except Exception as e:
                print(f"Error al procesar el artículo de Cronica {link}: {e}")

    finally:
        driver.quit()
    
    return scraped_articles