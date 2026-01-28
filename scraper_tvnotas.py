import time
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from utils import clean_article_text


def scrape_tvnotas(url):
    """
    Scraper de TVNotas usando Selenium
    """
    scraped_articles = []

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)

        # Esperar a que carguen notas
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "article"))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        article_links = []

        # TVNotas usa <article> con <a>
        for art in soup.find_all("article"):
            a = art.find("a", href=True)
            if a:
                href = a["href"]
                if href.startswith("/"):
                    article_links.append("https://www.tvnotas.com.mx" + href)
                elif href.startswith("http"):
                    article_links.append(href)

        article_links = list(set(article_links))
        print(f"Se encontraron {len(article_links)} enlaces en TVNotas.")

        for link in article_links:
            try:
                article = Article(link, language="es")
                article.download()
                article.parse()

                if not article.text or len(article.text) < 200:
                    continue

                cleaned_text = clean_article_text(article.text)

                scraped_articles.append({
                    "url": link,
                    "titulo": article.title,
                    "texto": cleaned_text,
                    "imagen_url": article.top_image
                })

                print(f"Artículo de TVNotas extraído: {article.title}")
                time.sleep(2)

            except Exception as e:
                print(f"Error artículo TVNotas {link}: {e}")

    finally:
        driver.quit()

    return scraped_articles
