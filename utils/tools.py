from pathlib import Path
import aiohttp
import logging
import os
import re
import typing as t

from markitdown import MarkItDown

logger = logging.getLogger(__name__)


async def fetch_uri(uri: str, save_path: str, with_jina: bool = False):
    """
    Fetch content from uri and save it.

    :param uri: the uri of the content.
    :param save_path: the path to save the content.
    :param with_jina: whether to use the jina proxy to parse the content.
    :return:
    """
    async with aiohttp.ClientSession() as session:
        # We use the r.jina.ai proxy to parse the origin content into markdown type.
        if with_jina:
            uri = "https://r.jina.ai/" + uri
        save_path = Path(save_path)
        logger.debug(f"Fetch uri: {uri}")
        async with session.get(uri) as response:
            content = await response.text()

            parent_path = save_path.parent
            if not parent_path.exists():
                logger.warning(
                    f"Parent path {parent_path} doesn't exist, try to create one."
                )
                os.mkdir(parent_path)

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
        os.mkdir(parent_path)

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
