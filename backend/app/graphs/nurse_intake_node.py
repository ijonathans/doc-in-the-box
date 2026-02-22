from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.graphs.common import dedupe, looks_like_emergency
from app.graphs.state import InterviewState


class NurseExtraction(BaseModel):
    chief_complaint: str | None = None
    timeline: str | None = None
    severity: str | None = None
    body_location: str | None = None
    pain_quality: str | None = None
    severity_0_10: int | None = None
    temporal_pattern: str | None = None
    trajectory: str | None = None
    modifying_factors: str | None = None
    onset: str | None = None
    precipitating_factors: str | None = None
    recurrent: bool | None = None
    sick_contacts: bool | None = None
    associated_symptoms: list[str] = Field(default_factory=list)
    red_flags_present: list[str] = Field(default_factory=list)
    red_flags_absent: list[str] = Field(default_factory=list)
    red_flags_unknown: list[str] = Field(default_factory=list)
    red_flags_screening_done: bool = False
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
                    "You are a triage nurse. Ask one question at a time. Prioritize safety and return structured data only. "
                    "Required for handoff (only these four): (1) chief_complaint – the main problem in the patient's words; (2) timeline – when it started, only when the patient has explicitly said so (e.g. 'since yesterday', 'for a week'). Do NOT infer from vague phrases like 'today' or 'recently'. "
                    "(3) body_location – where is the problem (e.g. chest, stomach, throat); (4) severity – use severity_0_10 (0-10) or severity (descriptive). "
                    "GUARDRAIL – Do NOT ask the patient 'where do you feel it?' when the location is obvious from the chief complaint. Set body_location yourself and move on. Obvious pairs: dizziness, lightheadedness, headache, head pain → head; runny nose, nasal congestion, stuffy nose → nose; sore eyes, eye pain, blurry vision, dry eyes → eyes; earache, ear pain → ear; sore throat, throat pain → throat. Only ask for location when the complaint could be in multiple places (e.g. pain, nausea, discomfort, pressure without a clear site). "
                    "Only when chief_complaint, timeline, body_location, and severity (or severity_0_10) are all present AND the user gives clear booking consent (e.g. 'yes', 'yes please', 'sure'), set booking_consent_given=true. "
                    "Set emergency_escalation=true only if the message describes an urgent red flag (chest pain, severe bleeding, trouble breathing, etc.).",
                ),
                (
                    "user",
                    "Current state: "
                    f"chief_complaint={state.get('chief_complaint')}, timeline={state.get('timeline')}, "
                    f"body_location={state.get('body_location')}, severity={state.get('severity')}, severity_0_10={state.get('severity_0_10')}. "
                    f"New patient message: {latest_message}\n"
                    "Update only fields the patient has clearly provided. Propose exactly one next question. "
                    "If timeline was not explicitly stated, leave timeline empty and ask when it started. "
                    "When all four required fields are present and user says yes/please/sure to booking, set booking_consent_given=true.",
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

    severity_0_10 = extraction.severity_0_10 if extraction.severity_0_10 is not None else state.get("severity_0_10")
    updated_state: dict[str, Any] = {
        "chief_complaint": extraction.chief_complaint or state.get("chief_complaint"),
        "timeline": extraction.timeline or state.get("timeline"),
        "severity": extraction.severity or state.get("severity"),
        "body_location": extraction.body_location or state.get("body_location"),
        "pain_quality": extraction.pain_quality or state.get("pain_quality"),
        "severity_0_10": severity_0_10,
        "temporal_pattern": extraction.temporal_pattern or state.get("temporal_pattern"),
        "trajectory": extraction.trajectory or state.get("trajectory"),
        "modifying_factors": extraction.modifying_factors or state.get("modifying_factors"),
        "onset": extraction.onset or state.get("onset"),
        "precipitating_factors": extraction.precipitating_factors or state.get("precipitating_factors"),
        "recurrent": extraction.recurrent if extraction.recurrent is not None else state.get("recurrent"),
        "sick_contacts": extraction.sick_contacts if extraction.sick_contacts is not None else state.get("sick_contacts"),
        "symptoms": dedupe(symptoms, extraction.associated_symptoms),
        "red_flags": {"present": present, "absent": absent, "unknown": unknown},
        "red_flags_screening_done": extraction.red_flags_screening_done or state.get("red_flags_screening_done") or False,
        "triage_level": extraction.provisional_triage_level or state.get("triage_level") or "undetermined",
        "needs_emergency": emergency_hit,
        "route_intent": "triage",
        "conversation_mode": "triage",
        "booking_confirmed": booking_confirmed,
        "assistant_reply": assistant_reply,
    }
    return updated_state
