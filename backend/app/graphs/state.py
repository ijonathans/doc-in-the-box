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
