import argparse
import unicodedata

from parser import parse_article
from scraper import DEFAULT_BASE_URL, search_news_links
from storage import save_to_csv
from utils import polite_delay


def normalize_text(text: str) -> str:
    """
    Normaliza texto para hacer comparaciones más flexibles.

    Convierte el texto a minúsculas y elimina acentos.
    Ejemplo:
        "Economía" -> "economia"
        "dólar" -> "dolar"
    """

    text = text.lower()
    text = unicodedata.normalize("NFD", text)

    return "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    )


def article_matches_keyword(article: dict, keyword: str) -> bool:
    """
    Verifica si la palabra clave aparece en datos relevantes de la noticia.

    Primero intenta encontrar la frase completa.
    Si la búsqueda tiene varias palabras, también acepta coincidencias donde
    aparezcan todas las palabras por separado.

    Ejemplo:
        "economia" coincide con textos que contengan:
        - "economia"

    Además se incluye la URL porque algunas búsquedas generales, como
    "economia", pueden aparecer en la sección de la noticia y no siempre
    en el título o descripción.
    """

    title = article.get("titulo") or ""
    description = article.get("descripcion") or ""
    url = article.get("url_noticia") or ""

    text_to_search = normalize_text(f"{title} {description} {url}")
    normalized_keyword = normalize_text(keyword)

    # Coincidencia directa de la frase completa.
    if normalized_keyword in text_to_search:
        return True

    # Coincidencia flexible: todas las palabras aparecen en el texto,
    # aunque no estén juntas.
    keyword_words = normalized_keyword.split()

    if len(keyword_words) > 1:
        return all(word in text_to_search for word in keyword_words)

    return False


def build_output_filename(keyword: str) -> str:
    """
    Genera el nombre del archivo CSV usando la palabra clave ingresada.

    Ejemplo:
        "dolar blue" -> data/noticias_dolar_blue.csv
    """

    clean_keyword = normalize_text(keyword.strip().replace(" ", "_"))

    return f"data/noticias_{clean_keyword}.csv"


def main():
    """
    Punto de entrada del script.

    Flujo general:
        1. Lee la palabra clave ingresada por el usuario.
        2. Busca enlaces de noticias en el portal.
        3. Entra a cada noticia encontrada.
        4. Extrae autor, fecha, título, descripción, imagen y URL.
        5. Filtra las noticias según la palabra clave.
        6. Guarda los resultados en un archivo CSV.
    """

    parser = argparse.ArgumentParser(
        description="Scraper de noticias por palabra clave."
    )

    parser.add_argument(
        "-k",
        "--keyword",
        help="Palabra clave para buscar noticias.",
        required=False,
    )

    parser.add_argument(
        "-n",
        "--max-results",
        help="Cantidad máxima de noticias a analizar.",
        type=int,
        default=10,
    )

    parser.add_argument(
        "-u",
        "--url",
        help="URL base del portal de noticias.",
        default=DEFAULT_BASE_URL,
    )

    args = parser.parse_args()

    keyword = args.keyword or input("Ingrese una palabra clave: ").strip()

    if not keyword:
        print("Debe ingresar una palabra clave.")
        return

    print(f"Buscando noticias relacionadas con: {keyword}")

    links = search_news_links(
        keyword=keyword,
        max_results=args.max_results,
        base_url=args.url,
    )

    print(f"Se encontraron {len(links)} enlaces para analizar.")

    if not links:
        print("No se encontraron enlaces de noticias.")
        return

    news = []

    for index, link in enumerate(links, start=1):
        try:
            print(f"[{index}/{len(links)}] Extrayendo: {link}")

            article = parse_article(link)

            if article_matches_keyword(article, keyword):
                news.append(article)
            else:
                print(
                    "La noticia fue descartada porque no coincide "
                    "con la palabra clave."
                )

            polite_delay(1)

        except Exception as error:
            print(f"No se pudo procesar la noticia: {link}")
            print(f"Error: {error}")

    if not news:
        print("No se encontraron noticias que coincidan con la palabra clave.")
        return

    output_file = build_output_filename(keyword)

    save_to_csv(news, output_file)

    print(f"Proceso finalizado. Archivo generado: {output_file}")


if __name__ == "__main__":
    main()