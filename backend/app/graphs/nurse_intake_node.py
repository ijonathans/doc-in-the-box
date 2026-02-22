from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from app.graphs.common import dedupe, looks_like_emergency
from app.graphs.state import InterviewState
from app.utils.demo_patient import DEMO_PATIENT
from app.utils.timeline_resolver import resolve_relative_timeline


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


async def nurse_intake_node(state: InterviewState, model: BaseChatModel | None) -> dict[str, Any]:
    latest_message = (state.get("latest_user_message") or "").strip()
    red_flags = state.get("red_flags") or {"present": [], "absent": [], "unknown": []}
    symptoms = state.get("symptoms") or []
    patient_first_name = (state.get("patient_context") or {}).get("first_name") or DEMO_PATIENT["first_name"]

    extraction = NurseExtraction()
    if model and latest_message:
        extractor = model.with_structured_output(NurseExtraction)
        extraction = await extractor.ainvoke(
            [
                (
                    "system",
                    f"""
                    You are a warm, deeply caring triage nurse. Ask only ONE question at a time. Prioritize patient safety and return structured data only.

                    The patient's first name is {patient_first_name}. Use it occasionally for a warm, personal touch (e.g. "Thanks, {patient_first_name}. When did the dizziness start?"). Do not overuse it.

                    TONE – Always sound human, compassionate, and emotionally present. Every single next_question must begin with brief empathy that acknowledges what the patient just shared. This acknowledgment must feel natural and supportive — never robotic or repetitive. Vary your wording.

                    Examples of appropriate warmth:
                    - 'Oh no, I’m really sorry you’re going through that.'
                    - 'That sounds really uncomfortable.'
                    - 'I understand, that must be frustrating.'
                    - 'That’s quite a long time to be dealing with this.'
                    - 'I’m sorry to hear that — that can feel scary.'
                    - 'Thanks for explaining that.'
                    - 'I can imagine that’s not pleasant.'
                    
                    After the empathy, gently transition into the next question.
                    Example:
                    If they say they feel dizzy, say:
                    'Oh no, I’m sorry you’re feeling that way. When did the dizziness start?'
                    NOT:
                    'When did it start?'

                    Never ask a cold, clinical question by itself. Never skip the empathy step. Keep warmth present in every reply, but remain concise.

                    Required for handoff (only these four fields):
                    (1) chief_complaint – the main problem in the patient’s own words.
                    (2) timeline – when it started, ONLY if the patient explicitly states timing (e.g., 'since yesterday', 'for three days'). If the patient says only a relative time (e.g. 'yesterday', '2 days ago'), set timeline to that phrase; the system will convert it to an exact date. Do NOT infer from vague phrases like 'recently' without a clear time. Once you have set timeline from the patient's reply, do not ask when it started again; move on to the next required question (location or severity).
                    (3) body_location – where the problem is located (e.g., chest, stomach, throat).
                    (4) severity – use severity_0_10 (0-10) if numeric is given, otherwise severity (descriptive).

                    GUARDRAIL – Do NOT ask 'where do you feel it?' when the body location is obvious from the chief complaint. Automatically set body_location and move forward.
                    Obvious mappings:
                    - dizziness, lightheadedness, headache, head pain → head
                    - runny nose, nasal congestion, stuffy nose → nose
                    - sore eyes, eye pain, blurry vision, dry eyes → eyes
                    - earache, ear pain → ear
                    - sore throat, throat pain → throat

                    Only ask for location when the complaint could occur in multiple areas (e.g., pain, pressure, discomfort, nausea without clear site).

                    Only when chief_complaint, timeline, body_location, AND severity (or severity_0_10) are all collected AND the patient gives clear booking consent (e.g., 'yes', 'yes please', 'sure'), set booking_consent_given=true.

                    Set emergency_escalation=true ONLY if the message clearly describes a red flag (e.g., chest pain, severe bleeding, trouble breathing, fainting, signs of stroke, etc.).
                """,
                ),
                (
                    "user",
                    "Current state: "
                    f"chief_complaint={state.get('chief_complaint')}, timeline={state.get('timeline')}, "
                    f"body_location={state.get('body_location')}, severity={state.get('severity')}, severity_0_10={state.get('severity_0_10')}. "
                    f"New patient message: {latest_message}\n"
                    "Update only fields the patient has clearly provided. Propose exactly one next question; always use a warm, caring tone and briefly acknowledge what they said before asking. "
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
    timeline = extraction.timeline or state.get("timeline")
    resolved = resolve_relative_timeline(timeline or latest_message or "")
    if resolved:
        timeline = resolved
    # When we just resolved timeline from "yesterday" etc., don't show the LLM's next_question (which often re-asks for timeline). Ask for the next missing field instead.
    if resolved and not emergency_hit and not extraction.booking_consent_given:
        _body_location = (extraction.body_location or state.get("body_location") or "").strip()
        _severity = (extraction.severity or state.get("severity") or "").strip()
        severity_sufficient = bool(_severity) or (severity_0_10 is not None and 0 <= severity_0_10 <= 10)
        if not _body_location:
            assistant_reply = "Thanks, that helps. Where do you feel it — for example, head, chest, or stomach?"
        elif not severity_sufficient:
            assistant_reply = "Thanks for the information. How would you rate it from 0 to 10, with 10 being the worst?"
        else:
            assistant_reply = "Thanks, that helps. Is there anything else you want to share about it?"
    updated_state: dict[str, Any] = {
        "chief_complaint": extraction.chief_complaint or state.get("chief_complaint"),
        "timeline": timeline,
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
