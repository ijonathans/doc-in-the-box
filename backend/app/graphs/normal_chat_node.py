from typing import Any

from langchain_openai import ChatOpenAI

from app.graphs.state import InterviewState


async def normal_chat_node(state: InterviewState, model: ChatOpenAI | None) -> dict[str, Any]:
    latest_message = (state.get("latest_user_message") or "").strip()
    if not model:
        return {
            "assistant_reply": "I can help with normal chat. If you describe a health symptom, I can switch to triage mode.",
            "next_action": "continue_questioning",
            "route_intent": "normal_chat",
            "conversation_mode": "normal_chat",
        }

    response = await model.ainvoke(
        [
            (
                "system",
                "You are a helpful assistant for general conversation. Keep responses clear and concise.",
            ),
            ("user", latest_message),
        ]
    )
    return {
        "assistant_reply": str(response.content).strip(),
        "next_action": "continue_questioning",
        "route_intent": "normal_chat",
        "conversation_mode": "normal_chat",
    }
