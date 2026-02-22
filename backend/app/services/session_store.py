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

    def _conv_key(self, conversation_id: str) -> str:
        return f"triage:conv_to_session:{conversation_id}"

    def _summary_key(self, session_id: str) -> str:
        return f"triage:call_summary:{session_id}"

    async def set_conversation_session(self, conversation_id: str, session_id: str) -> None:
        """Map ElevenLabs conversation_id to session_id for webhook lookup."""
        if not conversation_id or not session_id:
            return
        await self.redis.setex(self._conv_key(conversation_id), self.ttl_seconds, session_id)

    async def get_session_for_conversation(self, conversation_id: str) -> str | None:
        """Resolve session_id from ElevenLabs conversation_id."""
        if not conversation_id:
            return None
        return await self.redis.get(self._conv_key(conversation_id))

    async def set_pending_call_summary(
        self, session_id: str, summary: str, conversation_id: str = ""
    ) -> None:
        """Store a pending call summary to show in chat (consumed by Call_summarize node)."""
        if not session_id:
            return
        payload = json.dumps({"summary": summary, "conversation_id": conversation_id})
        await self.redis.setex(self._summary_key(session_id), self.ttl_seconds, payload)

    async def get_pending_call_summary(self, session_id: str) -> dict[str, Any] | None:
        """Get and clear the pending call summary for this session (consume once)."""
        if not session_id:
            return None
        key = self._summary_key(session_id)
        payload = await self.redis.get(key)
        if not payload:
            return None
        await self.redis.delete(key)
        return json.loads(payload)

    async def get(self, session_id: str) -> dict[str, Any] | None:
        payload = await self.redis.get(self._key(session_id))
        if not payload:
            return None
        return json.loads(payload)

    async def set(self, session_id: str, state: dict[str, Any]) -> None:
        payload = json.dumps(state)
        await self.redis.setex(self._key(session_id), self.ttl_seconds, payload)
