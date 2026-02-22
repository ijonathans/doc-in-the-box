import asyncio
import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.call_summary_events import publish_call_summary_ready, subscribe, unsubscribe
from app.services.chat_service import ChatService
from app.services.elevenlabs_call_agent import ElevenLabsCallAgent
from app.services.session_store import RedisSessionStore

MAX_SUMMARY_CHARS = 2000


def _summary_from_conversation_response(body: dict[str, Any]) -> str | None:
    """Build summary from ElevenLabs get_conversation response. Prefer analysis/summary, else transcript."""
    summary = ""
    analysis = body.get("analysis") or body.get("result", {}).get("analysis")
    if isinstance(analysis, dict):
        summary = (
            (analysis.get("summary") or analysis.get("transcript_summary") or analysis.get("call_summary") or "").strip()
        )
    if not summary and body.get("summary"):
        summary = (body["summary"] or "").strip()
    transcript = body.get("transcript")
    if not summary and isinstance(transcript, list) and transcript:
        lines = []
        for msg in transcript:
            role = msg.get("role", "") if isinstance(msg, dict) else ""
            text = msg.get("message", msg.get("text", "")) if isinstance(msg, dict) else str(msg)
            lines.append(f"{role}: {text}".strip())
        summary = "\n".join(lines)
        if len(summary) > MAX_SUMMARY_CHARS:
            summary = summary[:MAX_SUMMARY_CHARS] + "..."
    return summary.strip() or None


router = APIRouter()
chat_service = ChatService()

SSE_KEEPALIVE_SEC = 15
SSE_MAX_WAIT_SEC = 60 * 30


@router.post("/message", response_model=ChatResponse)
async def send_message(payload: ChatRequest) -> ChatResponse:
    result = await chat_service.send_message(message=payload.message, session_id=payload.session_id)
    return ChatResponse(**result)


@router.get("/pending-call-summary")
async def get_pending_call_summary(session_id: str) -> dict:
    """Peek at pending call summary (read-only). If none, try ElevenLabs conversation history by conversation_id."""
    store = RedisSessionStore()
    pending = await store.get_pending_call_summary_peek(session_id)
    if pending and (pending.get("summary") or "").strip():
        return {"summary": (pending.get("summary") or "").strip()}

    state = await store.get(session_id)
    if not state or not isinstance(state, dict):
        return {"summary": None}
    outbound = state.get("outbound_call") or {}
    conversation_id = (outbound.get("conversation_id") or "").strip()
    if not conversation_id:
        return {"summary": None}

    call_agent = ElevenLabsCallAgent()
    conv = await call_agent.get_conversation(conversation_id)
    summary = _summary_from_conversation_response(conv) if conv else None
    if summary:
        await store.set_pending_call_summary(session_id, summary, conversation_id)
        publish_call_summary_ready(session_id)
        return {"summary": summary}
    return {"summary": None}


@router.post("/consume-call-summary")
async def consume_call_summary(session_id: str) -> dict:
    """Consume (delete) the pending call summary for this session after the UI has shown it."""
    store = RedisSessionStore()
    await store.delete_pending_call_summary(session_id)
    return {"ok": True}


@router.get("/events")
async def call_summary_events(session_id: str) -> StreamingResponse:
    """
    SSE stream for this session. Sends event 'call_summary_ready' when the post-call webhook
    has stored the summary, so the frontend can show it immediately without polling.
    """
    if not session_id.strip():
        return StreamingResponse(
            iter([b"data: {\"error\": \"session_id required\"}\n\n"]),
            media_type="text/event-stream",
        )

    async def event_stream():
        queue = await subscribe(session_id)
        started = time.monotonic()
        try:
            while (time.monotonic() - started) < SSE_MAX_WAIT_SEC:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=SSE_KEEPALIVE_SEC)
                    event = msg.get("event", "message")
                    yield f"event: {event}\ndata: {{}}\n\n"
                    return
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await unsubscribe(session_id, queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
