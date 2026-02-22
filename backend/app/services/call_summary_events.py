"""In-memory broadcast for 'call summary ready' so the frontend can subscribe via SSE."""

import asyncio
from typing import Any

_listeners: dict[str, list[asyncio.Queue[Any]]] = {}
_lock = asyncio.Lock()


async def subscribe(session_id: str) -> asyncio.Queue[Any]:
    """Subscribe to call_summary_ready events for this session. Returns a queue that receives once."""
    async with _lock:
        if session_id not in _listeners:
            _listeners[session_id] = []
        q: asyncio.Queue[Any] = asyncio.Queue(maxsize=1)
        _listeners[session_id].append(q)
        return q


async def unsubscribe(session_id: str, queue: asyncio.Queue[Any]) -> None:
    """Remove a subscriber."""
    async with _lock:
        if session_id in _listeners:
            try:
                _listeners[session_id].remove(queue)
            except ValueError:
                pass
            if not _listeners[session_id]:
                del _listeners[session_id]


def publish_call_summary_ready(session_id: str) -> None:
    """Notify all subscribers for this session (call from webhook after storing summary)."""
    if session_id not in _listeners:
        return
    for q in _listeners[session_id]:
        try:
            q.put_nowait({"event": "call_summary_ready"})
        except asyncio.QueueFull:
            pass
