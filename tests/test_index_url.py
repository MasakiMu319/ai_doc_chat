import pytest

from utils.tools import index_documens


@pytest.mark.asyncio
async def test_index_url():
    await index_documens(url="https://trio.readthedocs.io/en/stable/index.html")
