import time
from urllib.parse import urljoin

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