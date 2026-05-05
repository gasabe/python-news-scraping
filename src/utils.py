import time
from functools import lru_cache
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

HEADERS = {"User-Agent": USER_AGENT}


def _build_robots_url(url: str) -> str | None:
    """
    Arma la URL del robots.txt para el dominio de una página.
    """

    parsed_url = urlparse(url)

    if not parsed_url.scheme or not parsed_url.netloc:
        return None

    return f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"


@lru_cache(maxsize=32)
def _load_robots_parser(robots_url: str) -> RobotFileParser | None:
    """
    Descarga y lee robots.txt.
    Lo cacheo para no pedir el mismo archivo en cada noticia.
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
    Revisa si robots.txt permite visitar una URL.
    Si robots.txt falla, aviso por consola y dejo continuar.
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
    Pide una página con requests y devuelve el HTML parseado con BeautifulSoup.
    """
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()

    # lxml es rápido y funciona bien con HTML real de sitios de noticias.
    return BeautifulSoup(response.text, "lxml")


def absolute_url(base_url: str, href: str) -> str:
    """
    Convierte un enlace relativo en URL completa.
    """
    return urljoin(base_url, href)


def polite_delay(seconds: float = 1.0) -> None:
    """
    Pausa simple entre pedidos para no consultar el sitio todo de golpe.
    """
    time.sleep(seconds)
