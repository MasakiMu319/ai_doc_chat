import time

import redis.asyncio as aioredis

from conf import settings
from utils.constants import BASE_REDIS_URI

LIMIT_REDIS_URI = f"{BASE_REDIS_URI}/{settings.redis.limitor.db}"


class Limitor:
    def __init__(self, key: str, period: int, max_count: int, timeout: float = 2.0):
        redis_pool = aioredis.BlockingConnectionPool.from_url(url=LIMIT_REDIS_URI)
        self.redis_client = aioredis.Redis.from_pool(connection_pool=redis_pool)
        self.key = key
        self.period = period
        self.max_count = max_count
        self.timeout = timeout

    async def is_action_allowed_with_block(self) -> bool:
        """
        Judge if the action is allowd.
        """
        start_time = time.perf_counter()
        while True:
            if time.perf_counter() - start_time > self.timeout:
                return False

            now = time.time()
            window_start = now - self.period
            key = (
                f"ratelimit:{self.key}"
                if not self.key.startswith("ralimit:")
                else self.key
            )
            async with self.redis_client.pipeline() as pipe:
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcount(key)
                pipe.zadd(key, {f"{now:.9f}": now})
                pipe.expire(key, self.period)

                _, current_count, _, _ = await pipe.execute()

                if current_count >= self.max_count:
                    pipe.zrem(key, f"{now:.9f}")
                    await pipe.execute()
                    continue
                return True
