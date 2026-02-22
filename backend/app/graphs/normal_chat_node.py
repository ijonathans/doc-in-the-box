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
                "You are a friendly healthcare assistant. You help with general health questions, wellness, and when to seek care. "
                "Keep responses clear, concise, and supportive. Do not give specific medical diagnoses or treatment; encourage users to see a provider when needed. "
                "If someone describes symptoms, you can offer comfort and suggest they use the triage flow in this app for a more detailed assessment.",
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
