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

from uuid import uuid4
from datetime import datetime, timezone

def save_research_memory(
    query: str,
    summary: str,
):
    """
    Save a research memory into Redis.

    Each memory is stored as its own item so it can later be searched,
    filtered, or retrieved independently.
    """

    store = get_redis_store()

    store.put(
        ("memories",),
        str(uuid4()),
        {
            "query": query,
            "summary": summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "type": "research_memory",
        },
    )

def search_research_memories(
    query: str | None = None,
    limit: int = 10,
):
    """
    Retrieve stored research memories.

    If a query is provided, RedisStore will use its search capability.
    Otherwise, return the most recent memories.
    """

    store = get_redis_store()

    results = store.search(
        ("memories",),
        query=query,
        limit=limit,
    )

    return results