from copy import deepcopy
from typing import Any, Literal, TypedDict


class PatientLocation(TypedDict):
    country: str | None
    state: str | None
    zip: str | None


class RiskModifiers(TypedDict):
    immunosuppressed: str
    blood_thinners: str


class PatientContext(TypedDict):
    age_range: str | None
    location: PatientLocation
    language: str
    pregnancy_postpartum: str
    risk_modifiers: RiskModifiers


class RedFlagsState(TypedDict):
    present: list[str]
    absent: list[str]
    unknown: list[str]


class ProviderSearchState(TypedDict):
    constraints: dict[str, Any]
    results: list[dict[str, Any]]


class BookingState(TypedDict):
    status: str


class OutboundCallState(TypedDict, total=False):
    """State for ElevenLabs outbound call flow (call clinics one by one until booked)."""
    next_clinic_index: int  # 0-based index into provider_search.results
    conversation_id: str  # ElevenLabs conversation_id from outbound-call response
    call_started: bool
    booking_result: str  # e.g. "booked", "not_available", "pending"


class InterviewState(TypedDict, total=False):
    session_id: str
    latest_user_message: str
    assistant_reply: str
    conversation_mode: Literal["normal_chat", "triage"]
    route_intent: Literal["normal_chat", "triage"]
    next_action: Literal["continue_questioning", "ready_for_handoff", "emergency_escalation"]
    needs_emergency: bool
    handoff_ready: bool
    missing_fields: list[str]
    patient_context: PatientContext
    chief_complaint: str | None
    timeline: str | None
    severity: str | None
    body_location: str | None
    pain_quality: str | None
    severity_0_10: int | None
    temporal_pattern: str | None
    trajectory: str | None
    modifying_factors: str | None
    onset: str | None
    precipitating_factors: str | None
    recurrent: bool | None
    sick_contacts: bool | None
    red_flags_screening_done: bool
    red_flags: RedFlagsState
    symptoms: list[str]
    pmh_meds_allergies: dict[str, Any]
    triage_level: str | None
    problem_representation: str | None
    differential: list[dict[str, Any]]
    kb_evidence: list[dict[str, Any]]
    care_plan: dict[str, Any]
    provider_search: ProviderSearchState
    booking: BookingState
    booking_confirmed: bool
    outbound_call: OutboundCallState
    reply_from_call_summary: bool  # Transient: do not persist; used to route to END after Call_summarize


DEFAULT_INTERVIEW_STATE: InterviewState = {
    "patient_context": {
        "age_range": None,
        "location": {"country": None, "state": None, "zip": None},
        "language": "en",
        "pregnancy_postpartum": "unknown",
        "risk_modifiers": {"immunosuppressed": "unknown", "blood_thinners": "unknown"},
    },
    "chief_complaint": None,
    "timeline": None,
    "severity": None,
    "body_location": None,
    "pain_quality": None,
    "severity_0_10": None,
    "temporal_pattern": None,
    "trajectory": None,
    "modifying_factors": None,
    "onset": None,
    "precipitating_factors": None,
    "recurrent": None,
    "sick_contacts": None,
    "red_flags_screening_done": False,
    "red_flags": {"present": [], "absent": [], "unknown": []},
    "symptoms": [],
    "pmh_meds_allergies": {},
    "triage_level": None,
    "problem_representation": None,
    "differential": [],
    "kb_evidence": [],
    "care_plan": {},
    "provider_search": {"constraints": {}, "results": []},
    "booking": {"status": "not_started"},
    "booking_confirmed": False,
    "outbound_call": {},
    "assistant_reply": "",
    "conversation_mode": "normal_chat",
    "route_intent": "normal_chat",
    "next_action": "continue_questioning",
    "needs_emergency": False,
    "handoff_ready": False,
    "missing_fields": [],
}


def create_default_interview_state(session_id: str) -> InterviewState:
    state = deepcopy(DEFAULT_INTERVIEW_STATE)
    state["session_id"] = session_id
    return state
