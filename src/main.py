import argparse
from datetime import datetime
import unicodedata

from parser import parse_article
from scraper import DEFAULT_BASE_URL, search_news_links
from storage import save_to_csv
from utils import can_fetch_url
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
        if all(word in text_to_search for word in keyword_words):
            return True

        # Los candidatos ya vienen del buscador del sitio. Para busquedas como
        # "boca juniors", una nota puede decir solo "Boca" y seguir siendo
        # relevante aunque no repita el nombre completo.
        significant_words = [
            word for word in keyword_words
            if len(word) >= 4
        ]

        return any(word in text_to_search for word in significant_words)

    return False


def parse_article_datetime(article: dict) -> datetime | None:
    """
    Convierte la fecha ISO 8601 de una noticia en un objeto datetime.

    Si la noticia no tiene fecha o la fecha no se puede interpretar, devuelve
    None para que el flujo pueda decidir si descarta o no ese articulo.
    """

    date_value = article.get("fecha_publicacion")

    if not date_value:
        return None

    try:
        return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
    except ValueError:
        return None


def article_matches_year(article: dict, year: int) -> bool:
    """
    Verifica si la noticia pertenece al anio indicado.
    """

    published_date = parse_article_datetime(article)

    if not published_date:
        return False

    return published_date.year == year


def article_timestamp(article: dict) -> float:
    """
    Devuelve un valor numerico para ordenar noticias por fecha.
    """

    published_date = parse_article_datetime(article)

    if not published_date:
        return 0

    return published_date.timestamp()


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
        help="Cantidad maxima de noticias a guardar.",
        type=int,
        default=10,
    )

    parser.add_argument(
        "-u",
        "--url",
        help=(
            "URL base de Perfil o plantilla de busqueda con {keyword}, "
            "por ejemplo https://example.com/buscar?q={keyword}."
        ),
        default=DEFAULT_BASE_URL,
    )

    parser.add_argument(
        "--year",
        help="Año de publicacion a guardar. Por defecto usa el año actual.",
        type=int,
        default=datetime.now().year,
    )

    parser.add_argument(
        "--all-years",
        help="Guardar noticias de cualquier año.",
        action="store_true",
    )

    args = parser.parse_args()

    keyword = args.keyword or input("Ingrese una palabra clave: ").strip()

    if not keyword:
        print("Debe ingresar una palabra clave.")
        return

    print(f"Buscando noticias relacionadas con: {keyword}")

    candidate_limit = max(args.max_results * 3, args.max_results)

    links = search_news_links(
        keyword=keyword,
        max_results=candidate_limit,
        base_url=args.url,
    )

    print(f"Se encontraron {len(links)} enlaces candidatos para analizar.")

    if not links:
        print("No se encontraron enlaces de noticias.")
        return

    news = []

    for index, link in enumerate(links, start=1):
        try:
            print(f"[{index}/{len(links)}] Extrayendo: {link}")

            if not can_fetch_url(link):
                print(f"robots.txt no permite acceder a esta noticia: {link}")
                continue

            article = parse_article(link)

            if not article_matches_keyword(article, keyword):
                print(
                    "La noticia fue descartada porque no coincide "
                    "con la palabra clave."
                )
                polite_delay(1)
                continue

            if not args.all_years and not article_matches_year(article, args.year):
                print(
                    "La noticia fue descartada porque no pertenece "
                    f"al anio {args.year}."
                )
                polite_delay(1)
                continue

            news.append(article)

            if len(news) >= args.max_results:
                break

            polite_delay(1)

        except Exception as error:
            print(f"No se pudo procesar la noticia: {link}")
            print(f"Error: {error}")

    if not news:
        print("No se encontraron noticias que coincidan con la palabra clave.")
        return

    output_file = build_output_filename(keyword)

    news.sort(key=article_timestamp, reverse=True)

    save_to_csv(news, output_file)

    print(f"Proceso finalizado. Archivo generado: {output_file}")


if __name__ == "__main__":
    main()
