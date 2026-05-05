from urllib.parse import quote, quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from utils import absolute_url
from utils import can_fetch_url


DEFAULT_BASE_URL = "https://www.perfil.com"


def build_search_url(
    keyword: str,
    base_url: str = DEFAULT_BASE_URL,
    page_number: int = 1,
) -> str:
    """
    Construye la URL del buscador de Perfil.

    Perfil usa Google Custom Search, y los resultados reales se cargan
    leyendo parámetros del hash de la URL:
        #gsc.tab=0&gsc.q=...&gsc.page=1
    """

    query_param = quote_plus(keyword)
    gsc_query = quote(keyword)
    base_url = base_url.rstrip("/")

    if "{keyword}" in base_url:
        return (
            base_url
            .replace("{keyword}", query_param)
            .replace("{page}", str(page_number))
        )

    return (
        f"{base_url}/buscador?q={query_param}"
        f"#gsc.tab=0&gsc.q={gsc_query}&gsc.page={page_number}&gsc.sort=date"
    )


def search_news_links(
    keyword: str,
    max_results: int = 10,
    base_url: str = DEFAULT_BASE_URL,
    max_pages: int = 5,
) -> list[str]:
    """
    Busca noticias en Perfil usando Playwright.

    Se usa Playwright porque los resultados del buscador se renderizan
    dinámicamente con JavaScript. Con requests solo se obtiene el HTML inicial
    y se pueden capturar links incorrectos, como las noticias de 'Las más leídas'.
    """

    links = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        )

        for page_number in range(1, max_pages + 1):
            search_url = build_search_url(keyword, base_url, page_number)

            print(f"URL de búsqueda: {search_url}")

            if can_fetch_url(search_url):
                print(f"robots.txt permite acceder a: {search_url}")
            else:
                print(f"robots.txt no permite acceder a: {search_url}")
                break

            page.goto(search_url, wait_until="networkidle", timeout=30000)

            try:
                page.wait_for_selector(".gsc-webResult", timeout=15000)
            except PlaywrightTimeoutError:
                print(
                    "No se pudieron cargar resultados con el selector de Perfil "
                    "(.gsc-webResult). Si cambiaste la URL, ese sitio probablemente "
                    "usa otra estructura de busqueda."
                )
                break

            result_links = page.locator(".gsc-webResult a.gs-title").evaluate_all(
                """
                elements => elements
                    .map(element => element.href)
                    .filter(href => href && href.includes('/noticias/'))
                """
            )

            new_links = 0

            for href in result_links:
                url = absolute_url(base_url, href)

                if url not in links:
                    links.append(url)
                    new_links += 1

                if len(links) >= max_results:
                    break

            if len(links) >= max_results or new_links == 0:
                break

        browser.close()

    return links
