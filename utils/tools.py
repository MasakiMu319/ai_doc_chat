import asyncio
from pathlib import Path
from urllib.parse import urlparse
import aiohttp
import logging
import logfire
import os
import re
import typing as t

from markitdown import MarkItDown

from core.connector.constants import WEB_CONNECTOR_TYPE
from core.connector.onyx import WebConnector
from utils.limitor import Limitor, retry_with_limitor_async

logger = logging.getLogger(__name__)


async def index_documens(url: str, use_jina: bool = False):
    """
    Index all pages found on the website and coverts them to markdown.

    :param url: the url to start the web connector.
    :return:
    """
    with logfire.span("index_documens"):
        logfire.info(f"Starting recursive web connector on {url}")
        web_connector = WebConnector(
            base_url=url,
            web_connector_type=WEB_CONNECTOR_TYPE.RECURSIVE,
        )
        documents = await web_connector.load_from_state()
        herf = urlparse(url)

        parent_path = Path(f"data/{herf.netloc}")
        if not use_jina:
            await asyncio.gather(
                *(
                    mark_it_down(
                        uri=doc.url,
                        save_path=parent_path.joinpath(doc.title),
                    )
                    for doc in documents
                )
            )
        else:
            jina_limitor = Limitor(key="jina", period=60, max_count=10, timeout=120)
            used_list = []
            lock = asyncio.Lock()
            async with asyncio.TaskGroup() as tg:
                for doc in documents:
                    async with lock:
                        if doc.url.split("/")[-1] in used_list or doc.url.endswith(
                            ".txt"
                        ):
                            continue
                        used_list.append(doc.url.split("/")[-1])

                    with logfire.span(f"fetching: {doc.url}"):
                        tg.create_task(
                            fetch_uri(
                                uri=doc.url,
                                save_path=parent_path.joinpath(doc.title),
                                with_jina=True,
                                limitor=jina_limitor,
                            )
                        )

        logfire.info("All documents have been indexed.")


@retry_with_limitor_async(max_retries=3, delay=1)
async def fetch_uri(
    uri: str, save_path: str, with_jina: bool = False, limitor: Limitor = None
):
    """
    Fetch content from uri and save it.

    :param uri: the uri of the content.
    :param save_path: the path to save the content.
    :param with_jina: whether to use the jina proxy to parse the content.
    :param limitor: the limitor to limit the number of requests.
    :return:
    """
    async with aiohttp.ClientSession() as session:
        # We use the r.jina.ai proxy to parse the origin content into markdown type.
        if with_jina:
            uri = "https://r.jina.ai/" + uri
        save_path = Path(save_path)
        logger.debug(f"Fetch uri: {uri}")
        default_headers = {"X-Engine": "readerlm-v2"}

        async with session.get(uri, headers=default_headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch {uri}")

            content = await response.text()
            contents = content.split("\n")
            content = "\n".join(contents[1:-1])

            parent_path = save_path.parent
            if not parent_path.exists():
                logger.warning(
                    f"Parent path {parent_path} doesn't exist, try to create one."
                )
                os.makedirs(parent_path, exist_ok=True)

            with open(save_path, "w") as f:
                f.write(content)
            logger.debug(f"Save content to {save_path}")


def list_files(dir_path: str | Path) -> t.List[str]:
    """
    List all files in a directory.

    :param dir_path: the directory path.
    :return: a list of file paths.
    """
    dir_path = dir_path if isinstance(dir_path, Path) else Path(dir_path)
    if not dir_path.is_dir():
        raise ValueError(f"{dir_path} is not a valid directory.")

    return [
        os.path.join(root, file)
        for root, dirs, files in os.walk(dir_path)
        for file in files
    ]


async def mark_it_down(uri: str, save_path: str):
    """
    Convert the content to markdown format.
    This function can download the content from the uri and convert it to markdown format automatically.
    But currently, images are not supported.Maybe we will add this feature in the future.

    :param uri: the uri of the content.
    :param save_path: the path to save the content.
    :return:
    """
    md = MarkItDown()
    result = md.convert_url(url=uri)
    save_path = Path(save_path)
    logger.debug(f"Fetch uri: {uri}")

    content = result.text_content

    parent_path = save_path.parent
    if not parent_path.exists():
        logger.warning(f"Parent path {parent_path} doesn't exist, try to create one.")
        os.makedirs(parent_path, exist_ok=True)

    with open(save_path, "w") as f:
        f.write(content)
    logger.debug(f"Save content to {save_path}")


async def clean_md(filename: str):
    """
    Clean the markdown file.
    Please note that this function is specifically designed for the markdown files from: https://www.lingchen.kim/art-design-pro/docs/.
    We very unrecommended to use this function for other markdown files.

    :param filename: the markdown file to clean.
    :return:
    """
    with open(filename, "r") as f:
        content = f.read()

    new_content = re.sub(r"^.*?(?=\n# )", "", content, flags=re.DOTALL)
    lines = new_content.split("\n")
    lines = lines[:-7]
    content = "\n".join(lines)
    with open(filename, "w") as f:
        f.write(content)
