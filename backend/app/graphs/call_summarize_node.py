"""
Call_summarize node: when a pending call summary exists for this session (set by ElevenLabs
post-call webhook), return it as assistant_reply and set reply_from_call_summary for routing to END.
"""

from __future__ import annotations

from typing import Any

from app.graphs.state import InterviewState
from app.services.session_store import RedisSessionStore


async def call_summarize_node(state: InterviewState) -> dict[str, Any]:
    """
    If the session has a pending call summary (from post-call webhook), return it as
    assistant_reply and reply_from_call_summary=True so the graph can END and show it in chat.
    Otherwise return {} and continue to router.
    """
    session_id = state.get("session_id")
    if not session_id:
        return {}
    store = RedisSessionStore()
    pending = await store.get_pending_call_summary(session_id)
    if not pending or not pending.get("summary"):
        return {}
    summary = (pending.get("summary") or "").strip()
    if not summary:
        return {}
    reply = "**Call summary**\n\n" + summary
    return {
        "assistant_reply": reply,
        "reply_from_call_summary": True,
    }
