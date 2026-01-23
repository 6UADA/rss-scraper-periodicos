
import os
import xml.etree.ElementTree as ET
from utils import clean_article_text

FORBES_DIR = r"d:\RSS\RSS\forbes"

def clean_xml_file(filepath):
    print(f"Processing {filepath}...")
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        modified = False

        for noticia in root.findall("noticia"):
            texto_elem = noticia.find("texto")
            if texto_elem is not None and texto_elem.text:
                original_text = texto_elem.text
                cleaned_text = clean_article_text(original_text)
                
                # Check if text actually changed (ignoring whitespace differences that might occur)
                if original_text.strip() != cleaned_text.strip():
                    texto_elem.text = cleaned_text
                    modified = True

        if modified:
            tree.write(filepath, encoding="utf-8", xml_declaration=True)
            print(f"  - Updated {filepath}")
        else:
            print(f"  - No changes needed for {filepath}")

    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    if not os.path.exists(FORBES_DIR):
        print(f"Directory not found: {FORBES_DIR}")
        return

    for filename in os.listdir(FORBES_DIR):
        if filename.endswith(".xml"):
            clean_xml_file(os.path.join(FORBES_DIR, filename))

if __name__ == "__main__":
    main()
