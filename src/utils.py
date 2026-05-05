import time
from functools import lru_cache
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

# Headers HTTP para simular una navegación normal desde un navegador.
# Esto ayuda a reducir la posibilidad de bloqueo por parte del sitio.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def _build_robots_url(url: str) -> str | None:
    """
    Construye la URL del robots.txt correspondiente a una URL del sitio.

    Ejemplo:
        https://www.perfil.com/noticias/test.phtml
        pasa a:
        https://www.perfil.com/robots.txt
    """

    parsed_url = urlparse(url)

    if not parsed_url.scheme or not parsed_url.netloc:
        return None

    return f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"


@lru_cache(maxsize=32)
def _load_robots_parser(robots_url: str) -> RobotFileParser | None:
    """
    Descarga y parsea un archivo robots.txt.

    Se cachea por dominio para no consultar el mismo robots.txt en cada noticia.
    Si el archivo no existe, se interpreta como que no hay restricciones
    declaradas por robots.txt.
    """

    parser = RobotFileParser()
    parser.set_url(robots_url)

    try:
        response = requests.get(robots_url, headers=HEADERS, timeout=10)

        if response.status_code == 404:
            parser.parse([])
            return parser

        response.raise_for_status()
        parser.parse(response.text.splitlines())
        return parser

    except requests.RequestException as error:
        print(f"No se pudo consultar robots.txt ({robots_url}): {error}")
        return None


def can_fetch_url(url: str, user_agent: str = HEADERS["User-Agent"]) -> bool:
    """
    Verifica si robots.txt permite visitar una URL.

    Si no se puede consultar robots.txt, se permite continuar pero se informa
    el problema por consola. Esto evita que una falla temporal del archivo
    bloquee todo el script.
    """

    robots_url = _build_robots_url(url)

    if not robots_url:
        return True

    parser = _load_robots_parser(robots_url)

    if parser is None:
        return True

    return parser.can_fetch(user_agent, url)


def get_soup(url: str, timeout: int = 10) -> BeautifulSoup:
    """
    Realiza una petición HTTP GET a una URL y devuelve el HTML parseado
    como un objeto BeautifulSoup.
    Args:
        url: URL a consultar.
        timeout: tiempo máximo de espera para la respuesta.

    Returns:
        Objeto BeautifulSoup con el contenido HTML de la página.

    Raises:
        HTTPError: si la respuesta del servidor no es exitosa.
        Timeout: si el sitio tarda más de lo esperado.
        RequestException: para otros errores de conexión.
    """
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()

    # Se usa lxml porque es rápido y robusto para parsear HTML.
    return BeautifulSoup(response.text, "lxml")


def absolute_url(base_url: str, href: str) -> str:
    """
    Convierte una URL relativa en una URL absoluta.

    Ejemplo:
        /noticias/economia/test.phtml
        pasa a:
        https://www.perfil.com/noticias/economia/test.phtml
    """
    return urljoin(base_url, href)


def polite_delay(seconds: float = 1.0) -> None:
    """
    Agrega una pausa entre requests para evitar sobrecargar el sitio. Esto es una práctica básica de scraping responsable.
    """
    time.sleep(seconds)
