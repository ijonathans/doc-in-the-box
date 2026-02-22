import json
from uuid import uuid4

from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.graphs.graph import TriageInterviewGraph
from app.graphs.state import create_default_interview_state
from app.services.session_store import RedisSessionStore


class ChatService:
    def __init__(self) -> None:
        self.model = (
            ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )
        self.graph = TriageInterviewGraph(self.model)
        self.session_store = RedisSessionStore()

    async def send_message(self, message: str, session_id: str | None = None) -> dict:
        resolved_session_id = session_id or str(uuid4())
        state = await self.session_store.get(resolved_session_id)
        if not state:
            state = create_default_interview_state(resolved_session_id)
        else:
            # Backward compatibility for sessions created before new fields existed.
            state.setdefault("conversation_mode", "normal_chat")
            state.setdefault("route_intent", "normal_chat")
            state.setdefault("booking_confirmed", False)
            state.setdefault("outbound_call", {})
            state.setdefault("body_location", None)
            state.setdefault("pain_quality", None)
            state.setdefault("severity_0_10", None)
            state.setdefault("temporal_pattern", None)
            state.setdefault("trajectory", None)
            state.setdefault("modifying_factors", None)
            state.setdefault("onset", None)
            state.setdefault("precipitating_factors", None)
            state.setdefault("recurrent", None)
            state.setdefault("sick_contacts", None)
            state.setdefault("red_flags_screening_done", False)

        state["session_id"] = resolved_session_id
        state["latest_user_message"] = message

        updated_state = await self.graph.run(state)
        # Do not persist transient routing flag (so next message does not immediately END)
        if "reply_from_call_summary" in updated_state:
            updated_state = dict(updated_state)
            del updated_state["reply_from_call_summary"]
        await self.session_store.set(resolved_session_id, updated_state)

        # Sanitize state for JSON response (avoid non-serializable values that could cause slow serialization or frontend freeze)
        try:
            state_for_response = json.loads(json.dumps(updated_state, default=str))
        except (TypeError, ValueError):
            state_for_response = dict(updated_state)

        outbound = updated_state.get("outbound_call") or {}
        return {
            "reply": updated_state.get("assistant_reply", ""),
            "session_id": resolved_session_id,
            "state": state_for_response,
            "needs_emergency": bool(updated_state.get("needs_emergency")),
            "handoff_ready": bool(updated_state.get("handoff_ready")),
            "outbound_call_started": bool(outbound.get("call_started")),
            "outbound_call_error": (outbound.get("last_result") or {}).get("message", ""),
        }
