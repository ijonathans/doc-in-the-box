import json
from typing import Any

from redis import asyncio as redis_async

from app.core.config import settings


class RedisSessionStore:
    def __init__(
        self,
        redis_url: str | None = None,
        ttl_seconds: int = 3600,
        redis_client: redis_async.Redis | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.redis = redis_client or redis_async.from_url(redis_url or settings.redis_url, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"triage:session:{session_id}"

    async def get(self, session_id: str) -> dict[str, Any] | None:
        payload = await self.redis.get(self._key(session_id))
        if not payload:
            return None
        return json.loads(payload)

    async def set(self, session_id: str, state: dict[str, Any]) -> None:
        payload = json.dumps(state)
        await self.redis.setex(self._key(session_id), self.ttl_seconds, payload)
