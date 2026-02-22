from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

from app.graphs.common import looks_like_health_concern
from app.graphs.state import InterviewState


class RouterDecision(BaseModel):
    route_intent: Literal["normal_chat", "triage"] = "normal_chat"
    rationale: str = ""


async def router_node(state: InterviewState, model: BaseChatModel | None) -> dict[str, Any]:
    latest_message = (state.get("latest_user_message") or "").strip()
    if state.get("conversation_mode") == "triage":
        return {
            "route_intent": "triage",
            "conversation_mode": "triage",
        }

    decision = RouterDecision(route_intent="triage" if looks_like_health_concern(latest_message) else "normal_chat")
    if model and latest_message:
        router = model.with_structured_output(RouterDecision)
        decision = await router.ainvoke(
            [
                (
                    "system",
                    "Route user intent. If the message includes health complaints, symptoms, medical concern, or triage need, "
                    "return triage. Otherwise return normal_chat.",
                ),
                ("user", latest_message),
            ]
        )

    resolved_intent = decision.route_intent
    return {
        "route_intent": resolved_intent,
        "conversation_mode": "triage" if resolved_intent == "triage" else "normal_chat",
    }
