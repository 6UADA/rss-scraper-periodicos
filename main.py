# main_scraper.py
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import time
import xml.etree.ElementTree as ET
import os

from scraper_cronica import scrape_cronica
from scraper_noventagrados import scrape_noventagrados
from scraper_netnoticias import scrape_netnoticias
from scraper_excelsior import scrape_excelsior
from scraper_forbes import scrape_forbes
from scraper_marca import scrape_marca
from scraper_unanimo import scrape_unanimo
from scraper_universal import scrape_universal
from scraper_jornada import scrape_jornada
from scraper_tvnotas import scrape_tvnotas

# Diccionario con las URLs de cada sección por periódico
SECTIONS = {

'cronica': {
        'mundo': "https://www.cronica.com.mx/mundo/",
        'nacional': "https://www.cronica.com.mx/nacional/",
        'espectaculos': "https://www.cronica.com.mx/escenario/"
    },

    'noventagrados': {
        'mundo': "https://www.noventagrados.com.mx/internacional.html",
        'nacional': "https://www.noventagrados.com.mx/nacional.html",
        'espectaculos': "https://www.noventagrados.com.mx/espectaculos.html"
    },

    'netnoticias': {
        'mundo': "https://netnoticias.mx/internacional",
        'nacional': "https://netnoticias.mx/nacional",
        'espectaculos': "https://netnoticias.mx/espectaculos"
    },

    'excelsior': {
        'mundo': "https://www.excelsior.com.mx/global",
        'nacional': "https://www.excelsior.com.mx/nacional",
        'espectaculos': "https://www.excelsior.com.mx/funcion"
    },

    'forbes': {
        'mundo': "https://forbes.com.mx/internacional/",
        'nacional': "https://forbes.com.mx/forbes-politica/",
        'espectaculos': "https://forbes.com.mx/forbes-life/all-access/"
    },

    'marca': {
        'futbol': "https://www.marca.com/mx/futbol.html?intcmp=MENUPROD&s_kw=mx-futbol"
    },

    'unanimo': {
        'futbol': "https://unanimodeportes.com/deportes/futbol/"
    },

    'universal': {
        'mundo': "https://www.eluniversal.com.mx/mundo/",
        'nacional': "https://www.eluniversal.com.mx/nacion/",
        'espectaculos': "https://www.eluniversal.com.mx/espectaculos/"
    },

    'jornada': {
        'espectaculos': "https://www.jornada.com.mx/categoria/espectaculos",
        'mundo': "https://www.jornada.com.mx/categoria/mundo",
        'capital': "https://www.jornada.com.mx/categoria/capital"
    },
    'tvnotas': {
        'espectaculos': "https://www.tvnotas.com.mx/espectaculos"
    }
}

def save_to_xml(data, folder_name, filename):
    """
    Guarda una lista de diccionarios en un archivo XML dentro de una carpeta específica.
    """
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    file_path = os.path.join(folder_name, filename)

    root = ET.Element('noticias')

    for articulo in data:
        item = ET.SubElement(root, 'noticia')

        ET.SubElement(item, 'url').text = articulo.get('url', '')
        ET.SubElement(item, 'titulo').text = articulo.get('titulo', '')
        ET.SubElement(item, 'texto').text = articulo.get('texto', '')
        ET.SubElement(item, 'imagen_url').text = articulo.get('imagen_url', '')

    tree = ET.ElementTree(root)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)

    print(f"\nArtículos guardados en '{file_path}'.")


if __name__ == "__main__":
    for site, sections in SECTIONS.items():
        print(f"\nIniciando extracción de {site.capitalize()}...")

        for section, url in sections.items():
            print(f"-> Raspando la sección '{section}'...")
            articles = []

            if site == 'cronica':
                articles = scrape_cronica(url)
                time.sleep(5)

            elif site == 'noventagrados':
                articles = scrape_noventagrados(url)

            elif site == 'netnoticias':
                articles = scrape_netnoticias(url)

            elif site == 'excelsior':
                articles = scrape_excelsior(url)

            elif site == 'forbes':
                articles = scrape_forbes(url)

            elif site == 'marca':
                articles = scrape_marca(url)[:10]

            elif site == 'unanimo':
                articles = scrape_unanimo(url)[:10]

            elif site == 'universal':                
                articles = scrape_universal(url)

            elif site == 'jornada':
                articles = scrape_jornada(url)

            elif site == 'tvnotas':
                articles = scrape_tvnotas(url)[:15]

            if articles:
                filename = f"{section}.xml"
                save_to_xml(articles, site, filename)
            else:
                print(f"No se pudieron extraer artículos de la sección '{section}' de {site.capitalize()}.")
