import json

from dateutil import parser as date_parser

from utils import get_soup


def _get_meta_content(soup, property_name: str):
    """
    Busca el contenido de una etiqueta meta.

    Algunos sitios usan:
        <meta property="og:title" content="...">

    Otros usan:
        <meta name="description" content="...">

    Esta función contempla ambos casos.
    """

    tag = soup.find("meta", property=property_name)
    if tag and tag.get("content"):
        return tag["content"].strip()

    tag = soup.find("meta", attrs={"name": property_name})
    if tag and tag.get("content"):
        return tag["content"].strip()

    return None


def _format_iso_date(date_value):
    """
    Convierte una fecha encontrada en el sitio al formato ISO 8601.

    Si no puede convertirla, devuelve el valor original para no perder el dato.
    """

    if not date_value:
        return None

    try:
        parsed_date = date_parser.parse(date_value)
        return parsed_date.isoformat()
    except Exception:
        return date_value


def _parse_json_ld(soup):
    """
    Intenta extraer información estructurada desde JSON-LD.

    Muchos portales de noticias incluyen datos estructurados en scripts:
        <script type="application/ld+json">

    Ahí suelen estar datos como:
        - headline
        - description
        - author
        - datePublished
        - image
    """

    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue

        # El JSON-LD puede venir como lista o como diccionario.
        if isinstance(data, list):
            items = data
        else:
            items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            article_type = item.get("@type", "")

            # A veces @type viene como lista y otras como string.
            if isinstance(article_type, list):
                is_article = any(
                    item_type in ["NewsArticle", "Article"]
                    for item_type in article_type
                )
            else:
                is_article = article_type in ["NewsArticle", "Article"]

            if is_article:
                return item

    return {}


def _normalize_structured_value(data, value_key: str):
    """
    Normaliza un dato que puede venir como string, diccionario o lista.
    """

    if isinstance(data, dict):
        return data.get(value_key)

    if isinstance(data, list) and data:
        first_item = data[0]
        return first_item.get(value_key) if isinstance(first_item, dict) else first_item

    return data


def _normalize_image(image):
    return _normalize_structured_value(image, "url")


def _normalize_author(author):
    return _normalize_structured_value(author, "name")


def parse_article(url: str) -> dict:
    """
    Extrae la información principal de una noticia.

    Args:
        url: URL de la noticia a procesar.

    Returns:
        Diccionario con los datos normalizados de la noticia.
    """

    soup = get_soup(url)

    # JSON-LD suele ser más estable que depender de clases CSS del sitio.
    json_ld = _parse_json_ld(soup)

    title = (
        json_ld.get("headline")
        or _get_meta_content(soup, "og:title")
        or (soup.find("h1").get_text(strip=True) if soup.find("h1") else None)
    )

    description = (
        json_ld.get("description")
        or _get_meta_content(soup, "og:description")
        or _get_meta_content(soup, "description")
    )

    image = json_ld.get("image") or _get_meta_content(soup, "og:image")
    image = _normalize_image(image)

    author = json_ld.get("author")
    author = _normalize_author(author)

    published_date = (
        json_ld.get("datePublished")
        or _get_meta_content(soup, "article:published_time")
        or _get_meta_content(soup, "date")
    )

    return {
        "autor": author,
        "fecha_publicacion": _format_iso_date(published_date),
        "titulo": title,
        "descripcion": description,
        "url_imagen": image,
        "url_noticia": url,
    }
