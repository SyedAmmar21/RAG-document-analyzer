import os
from redis import Redis
from langgraph.store.redis import RedisStore

_redis_store = None


def get_redis_store() -> RedisStore:
    """
    Returns a singleton RedisStore instance.

    The Redis indexes are created only once during the first initialization.
    All subsequent calls reuse the same Redis connection and store.
    """
    global _redis_store

    if _redis_store is None:
        redis_url = os.getenv(
            "REDIS_URL",
            "redis://rag-redis:6379"
        )

        client = Redis.from_url(redis_url)

        store = RedisStore(client)

        # Create Redis indexes if they do not already exist.
        store.setup()

        _redis_store = store

    return _redis_store