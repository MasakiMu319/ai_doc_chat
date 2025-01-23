from utils.limitor import Limitor
import pytest
import time
import asyncio

START, COUNT = None, 0


def task(i):
    global START
    if i > 20 and time.perf_counter() - START <= 60:
        raise Exception
    time.sleep(0.1)
    return i


@pytest.mark.asyncio
async def test_limitor():
    global START
    START = time.perf_counter()
    limitor = Limitor(key="test", period=60, max_count=20, timeout=120)

    async with asyncio.TaskGroup() as tg:
        for i in range(30):
            if await limitor.is_action_allowed_with_block():
                tg.create_task
