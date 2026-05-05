from urllib.parse import quote, quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from utils import USER_AGENT, absolute_url, can_fetch_url


DEFAULT_BASE_URL = "https://www.perfil.com"


def build_search_url(
    keyword: str,
    base_url: str = DEFAULT_BASE_URL,
    page_number: int = 1,
) -> str:
    """
    Arma la URL del buscador de Perfil.

    Perfil usa Google Custom Search, por eso además del query normal también
    agrego los parámetros del hash que usa el buscador.
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
    Busca enlaces de noticias usando Playwright.

    Lo uso solo en esta parte porque el buscador carga los resultados con
    JavaScript. Después, cada artículo se procesa con requests.
    """

    links = []
    search_url = build_search_url(keyword, base_url, page_number=1)

    print(f"URL de búsqueda: {search_url}")

    if not can_fetch_url(search_url):
        print(f"robots.txt no permite acceder a: {search_url}")
        return links

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(search_url, wait_until="networkidle", timeout=30000)

        try:
            page.wait_for_selector(".gsc-webResult", timeout=15000)
        except PlaywrightTimeoutError:
            print(
                "No se pudieron cargar resultados con el selector de Perfil "
                "(.gsc-webResult). Si cambiaste la URL, ese sitio probablemente "
                "usa otra estructura de búsqueda."
            )
            browser.close()
            return links

        for current_page in range(1, max_pages + 1):
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

            if len(links) >= max_results:
                break

            if current_page < max_pages:
                next_page_num = current_page + 1
                try:
                    page.locator(".gsc-cursor-page", has_text=str(next_page_num)).first.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                    page.wait_for_timeout(2000)
                except Exception:
                    break

        browser.close()

    return links
