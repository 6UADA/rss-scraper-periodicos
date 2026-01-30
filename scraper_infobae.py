import requests
from bs4 import BeautifulSoup
from newspaper import Article
import time
from utils import clean_article_text

def scrape_infobae(url):
    """
    Scraper de Infobae México - Espectáculos
    """
    scraped_articles = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Error accediendo a Infobae: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    article_links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/teleshow/" in href:
            if href.startswith("/"):
                href = "https://www.infobae.com" + href
            article_links.append(href)

    article_links = list(set(article_links))
    print(f"Se encontraron {len(article_links)} enlaces en Infobae.")

    for link in article_links:
        try:
            article = Article(link, language="es")
            article.download()
            article.parse()

            if not article.text or len(article.text) < 150:
                continue

            cleaned_text = clean_article_text(article.text)

            scraped_articles.append({
                "url": link,
                "titulo": article.title,
                "texto": cleaned_text,
                "imagen_url": article.top_image
            })

            print(f"Artículo Infobae extraído: {article.title}")
            time.sleep(1)

        except Exception as e:
            print(f"Error Infobae {link}: {e}")

    return scraped_articles
