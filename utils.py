import re

def clean_article_text(text):
    """
    Limpia el texto de un artículo eliminando líneas no deseadas como:
    - Redes sociales (Facebook, Twitter, etc.)
    - Frases como "Compartir", "Sigue nuestro Showcase", etc.
    - Atribuciones tipo "Con información de..."
    - Handles de redes sociales en formatos específicos (@user/x)
    """
    if not text:
        return ""

    # Compilar regex para eficiencia
    # "Con información de..." (insensible a mayúsculas/minúsculas)
    re_info_de = re.compile(r"con informaci[oó]n de", re.IGNORECASE)
    
    # Handles de redes sociales: 
    # (@Europarl_ES/x), (@Forsvarsmin/x), (@NormaOrtizRodr4/)
    # Busca patrones que empiecen con (@, tengan caracteres, y terminen en /x) o /)
    re_social_handle = re.compile(r"\(@[\w]+/[xX]?\)?") 

    # Frases específicas para filtrar (todo en minúsculas para comparación simple)
    spam_phrases = [
        "compartir", 
        "¿te gusta informarte por google news?", 
        "sigue nuestro showcase",
        "facebook", "twitter", "instagram", "síguenos", "fuente:", "cortesía:", 
        "x", # A veces 'x' solo aparece como red social
        "sigue el minuto a minuto", "en vivo por internet", "actualizar narración", 
        "canal: sin trasmisión", "te interesa", "marca.com", "se ampliará información",
        "pronóstico marca mx", "dónde ver", "horario",
        "con información de efe",
        "este artículo fue publicado originalmente por forbes us",
        "este artículo se publicó originalmente en forbes us",
        "con información de reuters"
        "Este artículo fue publicado originalmente en Forbes US"
        "Este artículo cuenta con información parcial publicada en Forbes US."
    ]

    clean_lines = []
    
    for line in text.split('\n'):
        stripped_line = line.strip()
        if not stripped_line:
            continue
            
        lower_line = stripped_line.lower()
        
        # 1. Filtro por frases exactas o substrings comunes
        if any(phrase in lower_line for phrase in spam_phrases):
            continue
            
        # 2. Filtro por "Con información de"
        if re_info_de.search(lower_line):
            continue
            
        # 3. Filtro por handles de redes sociales (captions de fotos, etc.)
        if re_social_handle.search(line):
            continue

        clean_lines.append(stripped_line)

    return "\n".join(clean_lines)
