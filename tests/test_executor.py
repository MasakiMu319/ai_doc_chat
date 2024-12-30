import time
import aiohttp
import pytest


from utils.executor import Executor


@pytest.mark.asyncio
async def test_executor():
    executor = Executor()
    await executor.start()

    async def fetch_url():
        async with aiohttp.ClientSession() as session:
            async with session.get("http://example.com") as response:
                return await response.text()

    start = time.perf_counter()
    await executor.submit(fetch_url)
    result = await executor.results()
    end = time.perf_counter()
    print(f"Time: {end - start}")
    assert len(result) == 1

    await executor.start()
    start = time.perf_counter()
    [await executor.submit(fetch_url) for _ in range(100)]
    result = await executor.results()
    end = time.perf_counter()
    print(f"100 * Time: {end - start}")
    assert len(result) == 100
