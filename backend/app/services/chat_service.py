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
            # Backward compatibility for sessions created before router fields existed.
            state.setdefault("conversation_mode", "normal_chat")
            state.setdefault("route_intent", "normal_chat")

        state["session_id"] = resolved_session_id
        state["latest_user_message"] = message

        updated_state = await self.graph.run(state)
        await self.session_store.set(resolved_session_id, updated_state)

        return {
            "reply": updated_state.get("assistant_reply", ""),
            "session_id": resolved_session_id,
            "state": updated_state,
            "needs_emergency": bool(updated_state.get("needs_emergency")),
            "handoff_ready": bool(updated_state.get("handoff_ready")),
        }
