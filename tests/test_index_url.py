import logfire
import pytest
from conf import settings

from utils.tools import index_documens


@pytest.mark.asyncio
async def test_index_url():
    logfire.configure(
        token=settings.log.LOGFIRE_TOKEN,
    )
    await index_documens(url="https://anyio.readthedocs.io/en/stable/", use_jina=True)
