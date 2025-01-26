import pytest
from utils.concurrency import iterate_in_threadpool


@pytest.mark.asyncio
async def test_iterate_in_threadpool():
    def mock_iterator():
        for i in range(5):
            yield i

    async for item in iterate_in_threadpool(mock_iterator()):
        print(item)
        assert item in range(5)
