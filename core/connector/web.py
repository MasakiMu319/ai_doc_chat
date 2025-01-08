import asyncio
from pprint import pprint
import typing as t
import logging


from bs4 import BeautifulSoup

from core.connector.constants import WEB_CONNECTOR_TYPE
from utils import web

logger = logging.getLogger(__name__)


class WebConnector:
    def __init__(
        self,
        base_url: str,
        web_connector_type: WEB_CONNECTOR_TYPE,
        mintlify_cleanup: bool = True,
    ):
        """
        Initialize the web connector.

        :param base_url: The base URL to start the web connector.
        :param web_connector_type: The type of web connector to use.
        :param mintlify_cleanup: Whether to clean up specific HTML tags.
        """
        self.mintlify_cleanup = mintlify_cleanup
        self.recursive = False

        logger.info(f"Starting recursive web connector on {base_url}")

        match web_connector_type:
            case WEB_CONNECTOR_TYPE.RECURSIVE:
                self.recursive = True
                self.to_visit_list = [web.ensure_valid_url(base_url)]
            case WEB_CONNECTOR_TYPE.SINGLE:
                self.to_visit_list = [web.ensure_valid_url(base_url)]
            case WEB_CONNECTOR_TYPE.SITEMAP:
                self.to_visit_list = web.extract_urls_from_sitemap(
                    web.ensure_valid_url(base_url)
                )
            case WEB_CONNECTOR_TYPE.UPLOAD:
                self.to_visit_list = web.read_urls_from_file(base_url)
            case _:
                raise ValueError(f"Unknown web connector type: {web_connector_type}")

    async def load_from_state(self):
        """
        Index all pages found on the website and coverts them to markdown.
        """
        visited_links: t.Set[str] = set()
        to_visit: t.List[str] = self.to_visit_list

        if to_visit is None or len(to_visit) == 0:
            logger.error("No pages to visit.")
            raise ValueError("No pages to visit.")

        base_url = to_visit[0]
        documents = []

        # Needed to report error
        last_error = None

        playwright, context = await web.start_playwright()
        restart_playwright = False
        while to_visit:
            current_url = to_visit.pop()
            if current_url in visited_links:
                continue
            visited_links.add(current_url)

            try:
                # Check if the URL is valid.
                web.protected_url_check(current_url)
            except Exception as e:
                last_error = f"Invalid URL {current_url} due to {e}"
                logger.warning(last_error)
                continue

            logger.info(f"Visiting {current_url}")

            try:
                web.check_internet_connection(current_url)
                if restart_playwright:
                    playwright, context = await web.start_playwright()
                    restart_playwright = False

                page = await context.new_page()
                page_response = await page.goto(current_url)

                final_page = page.url
                if final_page != current_url:
                    logger.info(f"Redirected to {final_page}")
                    web.protected_url_check(final_page)
                    current_url = final_page
                    if current_url in visited_links:
                        logger.info("Redirected page already indexed")
                        continue
                    visited_links.add(current_url)

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                if self.recursive:
                    internal_links = web.get_internal_links(base_url, current_url, soup)
                    for link in internal_links:
                        if link not in visited_links:
                            to_visit.append(link)

                if page_response and str(page_response.status)[0] in ("4", "5"):
                    last_error = f"Skipped indexing {current_url} due to HTTP {page_response.status} response"
                    logger.info(last_error)
                    continue

                parsed_html = web.web_html_cleanup(soup, self.mintlify_cleanup)
                parsed_html.url = current_url
                documents.append(parsed_html)
            except Exception as e:
                last_error = f"Error indexing {current_url} due to {e}"
                logger.error(last_error)
                continue

        await playwright.stop()
        return documents


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    web_connector = WebConnector(
        base_url="https://www.lingchen.kim/art-design-pro/docs/guide/essentials/route.html",
        web_connector_type=WEB_CONNECTOR_TYPE.RECURSIVE,
    )
    documents = asyncio.run(web_connector.load_from_state())
    urls = [doc.url for doc in documents]
    pprint(urls)
    pprint(documents[0])
    # print(len(documents))
