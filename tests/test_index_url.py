import pytest

from utils.tools import index_documens


@pytest.mark.asyncio
async def test_index_url():
    await index_documens(
        url="https://www.lingchen.kim/art-design-pro/docs/guide/essentials/route.html"
    )
