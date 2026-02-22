from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from app.graphs.state import InterviewState
from app.utils.demo_patient import DEMO_PATIENT


async def normal_chat_node(state: InterviewState, model: BaseChatModel | None) -> dict[str, Any]:
    latest_message = (state.get("latest_user_message") or "").strip()
    patient_first_name = (state.get("patient_context") or {}).get("first_name") or DEMO_PATIENT["first_name"]
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
                f"You are a warm, caring nurse-style assistant. Speak in a gentle, reassuring way — like a nurse at the front desk who truly cares. "
                f"The patient's first name is {patient_first_name}. Use it when appropriate for a warm, personal tone. "
                "Use a warm tone: acknowledge how the person might be feeling, use 'we' when helpful (e.g. 'We can figure this out'), and offer comfort before information. "
                "Help with general health questions, wellness, and when to seek care. Do not give specific medical diagnoses or treatment; encourage seeing a provider when needed. "
                "If someone describes symptoms, validate their concern, offer brief comfort, and suggest they use the triage flow in this app for a more thorough assessment.",
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
