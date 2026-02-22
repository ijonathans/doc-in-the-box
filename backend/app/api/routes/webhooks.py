"""Webhook endpoints for external services (e.g. ElevenLabs post-call)."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services.session_store import RedisSessionStore

router = APIRouter()


def _extract_summary_from_payload(body: dict[str, Any]) -> str:
    """Build chat summary from ElevenLabs post-call payload. Prefer analysis/summary, else transcript."""
    summary = ""
    analysis = body.get("analysis") or body.get("result", {}).get("analysis")
    if isinstance(analysis, dict):
        summary = (
            analysis.get("summary")
            or analysis.get("transcript_summary")
            or analysis.get("call_summary")
            or ""
        )
    if not summary and "summary" in body:
        summary = body["summary"] or ""
    transcript = body.get("transcript") or body.get("transcript_text") or ""
    if isinstance(transcript, list):
        transcript = " ".join(
            str(t.get("text", t) if isinstance(t, dict) else t) for t in transcript
        )
    if not summary and transcript:
        summary = transcript[:2000] + ("..." if len(transcript) > 2000 else "")
    if not summary:
        summary = "Call completed. No transcript or summary available."
    return summary.strip()


def _extract_conversation_id(body: dict[str, Any]) -> str:
    """Get conversation_id from webhook payload."""
    return (
        body.get("conversation_id")
        or body.get("conversationId")
        or body.get("id")
        or ""
    )


@router.post("/elevenlabs/post-call")
async def elevenlabs_post_call(request: Request) -> JSONResponse:
    """
    Receive ElevenLabs post-call webhook (call ended, analysis/transcript ready).
    Look up session from conversation_id, store pending call summary for Call_summarize node.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    conversation_id = _extract_conversation_id(body)
    if not conversation_id:
        return JSONResponse(content={"ok": True, "message": "No conversation_id"}, status_code=200)
    store = RedisSessionStore()
    session_id = await store.get_session_for_conversation(conversation_id)
    if not session_id:
        return JSONResponse(content={"ok": True, "message": "Session not found"}, status_code=200)
    summary = _extract_summary_from_payload(body)
    await store.set_pending_call_summary(session_id, summary, conversation_id)
    return JSONResponse(content={"ok": True, "session_id": session_id}, status_code=200)
