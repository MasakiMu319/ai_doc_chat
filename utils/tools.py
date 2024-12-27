from pathlib import Path
import aiohttp
import logging
import os

logger = logging.getLogger(__name__)


async def fetch_uri(uri: str, save_path: str):
    """
    Fetch content from uri and save it.

    :param uri: the uri of the content.
    :param save_path: the path to save the content.
    :return:
    """
    async with aiohttp.ClientSession() as session:
        # We use the r.jina.ai proxy to parse the origin content into markdown type.
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
