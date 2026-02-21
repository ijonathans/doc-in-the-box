from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.graphs.common import dedupe, looks_like_emergency
from app.graphs.state import InterviewState


class NurseExtraction(BaseModel):
    chief_complaint: str | None = None
    timeline: str | None = None
    severity: str | None = None
    associated_symptoms: list[str] = Field(default_factory=list)
    red_flags_present: list[str] = Field(default_factory=list)
    red_flags_absent: list[str] = Field(default_factory=list)
    red_flags_unknown: list[str] = Field(default_factory=list)
    provisional_triage_level: str | None = None
    emergency_escalation: bool = False
    booking_consent_given: bool = False
    next_question: str = "What symptom is most concerning right now?"


async def nurse_intake_node(state: InterviewState, model: ChatOpenAI | None) -> dict[str, Any]:
    latest_message = (state.get("latest_user_message") or "").strip()
    red_flags = state.get("red_flags") or {"present": [], "absent": [], "unknown": []}
    symptoms = state.get("symptoms") or []

    extraction = NurseExtraction()
    if model and latest_message:
        extractor = model.with_structured_output(NurseExtraction)
        extraction = await extractor.ainvoke(
            [
                (
                    "system",
                    "You are a triage nurse. Ask one question at a time, prioritize safety, and return structured data only. "
                    "Required for handoff: (1) chief_complaint – the main problem in the patient's words; (2) timeline – when it started, only when the patient has explicitly said so (e.g. 'since yesterday', 'for a week'). "
                    "Do NOT infer or guess timeline from vague phrases like 'today' or 'recently'. Only set timeline when the user clearly states when the problem started. "
                    "If chief_complaint is vague (e.g. only 'not feeling well'), ask what the main problem is. If timeline is missing, your next_question must ask when it started. "
                    "When chief_complaint AND timeline are already present and the user message is a clear consent to book (e.g. 'yes', 'yes please', 'sure', 'please do', 'go ahead'), set booking_consent_given=true. "
                    "For the first question when the patient reports feeling unwell (e.g. dizzy), you may be empathetic: e.g. 'Sorry to hear that. Since when did you feel the dizziness?' "
                    "Set emergency_escalation=true only if the message describes an urgent red flag (chest pain, severe bleeding, etc.).",
                ),
                (
                    "user",
                    f"Current state: chief_complaint={state.get('chief_complaint')}, timeline={state.get('timeline')}\n"
                    f"New patient message: {latest_message}\n"
                    "Update only fields the patient has clearly provided. Propose exactly one next question. "
                    "If timeline was not explicitly stated by the patient, leave timeline empty and ask when it started. "
                    "If we already have complaint and timeline and the user is saying yes/please/sure to booking, set booking_consent_given=true.",
                ),
            ]
        )

    emergency_hit = extraction.emergency_escalation or looks_like_emergency(latest_message)
    present = dedupe(red_flags.get("present", []), extraction.red_flags_present)
    absent = dedupe(red_flags.get("absent", []), extraction.red_flags_absent)
    unknown = dedupe(red_flags.get("unknown", []), extraction.red_flags_unknown)

    if emergency_hit and not present:
        present = dedupe(present, [latest_message or "possible emergency red flag"])

    booking_confirmed = bool(extraction.booking_consent_given or state.get("booking_confirmed"))
    assistant_reply: str
    if emergency_hit:
        assistant_reply = "I am concerned this could be an emergency. Call your local emergency number now."
    elif extraction.booking_consent_given:
        assistant_reply = "I'll look that up for you."
    else:
        assistant_reply = extraction.next_question

    updated_state: dict[str, Any] = {
        "chief_complaint": extraction.chief_complaint or state.get("chief_complaint"),
        "timeline": extraction.timeline or state.get("timeline"),
        "severity": extraction.severity or state.get("severity"),
        "symptoms": dedupe(symptoms, extraction.associated_symptoms),
        "red_flags": {"present": present, "absent": absent, "unknown": unknown},
        "triage_level": extraction.provisional_triage_level or state.get("triage_level") or "undetermined",
        "needs_emergency": emergency_hit,
        "route_intent": "triage",
        "conversation_mode": "triage",
        "booking_confirmed": booking_confirmed,
        "assistant_reply": assistant_reply,
    }
    return updated_state
