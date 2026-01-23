import requests
import time
from bs4 import BeautifulSoup
from newspaper import Article
from utils import clean_article_text

HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_jornada(url):
    """
    Scraper de La Jornada (HTML estático, no Selenium)
    """
    scraped_articles = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        article_links = []

        # 🔥 SELECTOR REAL DE LA JORNADA
        for h3 in soup.select("h3"):
            a = h3.find("a", href=True)
            if a:
                href = a["href"]
                if href.startswith("/"):
                    article_links.append("https://www.jornada.com.mx" + href)
                elif href.startswith("http"):
                    article_links.append(href)

        article_links = list(set(article_links))
        print(f"Se encontraron {len(article_links)} enlaces en La Jornada.")

        for link in article_links:
            try:
                art = Article(link, language="es")
                art.download()
                art.parse()

                if not art.text or len(art.text) < 150:
                    continue

                cleaned_text = clean_article_text(art.text)

                scraped_articles.append({
                    "url": link,
                    "titulo": art.title,
                    "texto": cleaned_text,
                    "imagen_url": art.top_image
                })

                print(f"Artículo de La Jornada extraído: {art.title}")
                time.sleep(2)

            except Exception as e:
                print(f"Error artículo Jornada {link}: {e}")

    except Exception as e:
        print(f"Error cargando categoría Jornada: {e}")

    return scraped_articles
