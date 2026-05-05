from urllib.parse import quote, quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from utils import absolute_url


DEFAULT_BASE_URL = "https://www.perfil.com"


def build_search_url(keyword: str, base_url: str = DEFAULT_BASE_URL) -> str:
    """
    Construye la URL del buscador de Perfil.

    Perfil usa Google Custom Search, y los resultados reales se cargan
    leyendo parámetros del hash de la URL:
        #gsc.tab=0&gsc.q=...&gsc.page=1
    """

    query_param = quote_plus(keyword)
    gsc_query = quote(keyword)

    return (
        f"{base_url}/buscador?q={query_param}"
        f"#gsc.tab=0&gsc.q={gsc_query}&gsc.page=1"
    )


def search_news_links(
    keyword: str,
    max_results: int = 10,
    base_url: str = DEFAULT_BASE_URL,
) -> list[str]:
    """
    Busca noticias en Perfil usando Playwright.

    Se usa Playwright porque los resultados del buscador se renderizan
    dinámicamente con JavaScript. Con requests solo se obtiene el HTML inicial
    y se pueden capturar links incorrectos, como las noticias de 'Las más leídas'.
    """

    search_url = build_search_url(keyword, base_url)

    print(f"URL de búsqueda: {search_url}")

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

        page.goto(search_url, wait_until="networkidle", timeout=30000)

        try:
            page.wait_for_selector(".gsc-webResult", timeout=15000)
        except PlaywrightTimeoutError:
            print("No se pudieron cargar los resultados dinámicos del buscador.")
            browser.close()
            return []

        result_links = page.locator(".gsc-webResult a.gs-title").evaluate_all(
            """
            elements => elements
                .map(element => element.href)
                .filter(href => href && href.includes('/noticias/'))
            """
        )

        browser.close()

    for href in result_links:
        url = absolute_url(base_url, href)

        if url not in links:
            links.append(url)

        if len(links) >= max_results:
            break

    return links