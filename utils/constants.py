from urllib.parse import quote_plus

from conf import settings

BASE_REDIS_URI = f"redis://{settings.redis.username}:{quote_plus(settings.redis.password)}@{settings.redis.host}:{settings.redis.port}"

SEMAPHORE = 10
