from __future__ import annotations

from redis.asyncio import Redis

from app.settings import settings


def create_redis() -> Redis:
    # decode_responses=False -> bytes, safer for arbitrary payloads
    return Redis.from_url(settings.REDIS_URL, decode_responses=False)


async def close_redis(r: Redis | None) -> None:
    if r is None:
        return
    try:
        await r.close()
    except Exception:
        pass
