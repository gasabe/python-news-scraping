import argparse
from datetime import datetime
import unicodedata

from parser import parse_article
from scraper import DEFAULT_BASE_URL, search_news_links
from storage import save_to_csv
from utils import can_fetch_url, polite_delay


def normalize_text(text: str) -> str:
    """
    Deja el texto en un formato más fácil de comparar.
    Así "Economía" y "economia" se toman como lo mismo.
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
    Decide si una noticia queda dentro de la búsqueda.

    La consigna pide que la palabra clave aparezca en el título o en la
    descripción.
    """

    title = article.get("titulo") or ""
    description = article.get("descripcion") or ""

    normalized_title = normalize_text(title)
    normalized_description = normalize_text(description)
    normalized_keyword = normalize_text(keyword)

    # Primero pruebo con la frase completa.
    if (
        normalized_keyword in normalized_title
        or normalized_keyword in normalized_description
    ):
        return True

    # Si son varias palabras, acepto cualquier coincidencia.
    keyword_words = normalized_keyword.split()

    if len(keyword_words) > 1:
        return any(
            word in normalized_title or word in normalized_description
            for word in keyword_words
        )

    return False


def parse_article_datetime(article: dict) -> datetime | None:
    """
    Convierte la fecha guardada en la noticia a datetime.
    Si falta o no se puede leer, devuelvo None.
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
    Verifica si la noticia pertenece al año indicado.
    """

    published_date = parse_article_datetime(article)

    if not published_date:
        return False

    return published_date.year == year


def article_timestamp(article: dict) -> float:
    """
    Devuelve un número para ordenar las noticias por fecha.
    """

    published_date = parse_article_datetime(article)

    if not published_date:
        return 0

    return published_date.timestamp()


def build_output_filename(keyword: str) -> str:
    """
    Arma el nombre del CSV a partir de la palabra buscada.
    """

    clean_keyword = normalize_text(keyword.strip().replace(" ", "_"))

    return f"data/noticias_{clean_keyword}.csv"


def main():
    """
    Coordina el flujo principal: leer argumentos, buscar enlaces, extraer
    artículos, filtrar resultados y guardar el CSV.
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
            "URL base de Perfil o plantilla de búsqueda con {keyword}, "
            "por ejemplo https://example.com/buscar?q={keyword}."
        ),
        default=DEFAULT_BASE_URL,
    )

    parser.add_argument(
        "--year",
        help="Año de publicación a guardar. Si no se indica, no filtra por año.",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--all-years",
        help="Ignorar el filtro por año si se combina con --year.",
        action="store_true",
    )

    args = parser.parse_args()

    keyword = args.keyword or input("Ingrese una palabra clave: ").strip()

    if not keyword:
        print("Debe ingresar una palabra clave.")
        return

    print(f"Buscando noticias relacionadas con: {keyword}")

    candidate_limit = args.max_results * 3

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
                continue

            if (
                args.year is not None
                and not args.all_years
                and not article_matches_year(article, args.year)
            ):
                print(
                    "La noticia fue descartada porque no pertenece "
                    f"al año {args.year}."
                )
                continue

            news.append(article)

            if len(news) >= args.max_results:
                break

        except Exception as error:
            print(f"No se pudo procesar la noticia: {link}")
            print(f"Error: {error}")

        print("Esperando antes de continuar...")
        polite_delay(1)

    if not news:
        print("No se encontraron noticias que coincidan con la palabra clave.")
        return

    output_file = build_output_filename(keyword)

    news.sort(key=article_timestamp, reverse=True)

    save_to_csv(news, output_file)

    print(f"Proceso finalizado. Archivo generado: {output_file}")


if __name__ == "__main__":
    main()
