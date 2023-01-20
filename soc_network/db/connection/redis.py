import redis
from soc_network.config import get_settings


async def get_redis():
    return redis.Redis(
        host=get_settings().REDIS_HOST,
        port=get_settings().REDIS_PORT,
        db=get_settings().REDIS_CACHE_DB,
    )