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
                    "First prioritize collecting chief complaint and when it started (timeline). "
                    "Set emergency_escalation=true if any urgent red flag appears.",
                ),
                (
                    "user",
                    f"Current state: {state}\n"
                    f"New patient message: {latest_message}\n"
                    "Update known intake fields, red flags, provisional triage level, and propose exactly one next question. "
                    "If either chief_complaint or timeline is missing, ask specifically for the missing one.",
                ),
            ]
        )

    emergency_hit = extraction.emergency_escalation or looks_like_emergency(latest_message)
    present = dedupe(red_flags.get("present", []), extraction.red_flags_present)
    absent = dedupe(red_flags.get("absent", []), extraction.red_flags_absent)
    unknown = dedupe(red_flags.get("unknown", []), extraction.red_flags_unknown)

    if emergency_hit and not present:
        present = dedupe(present, [latest_message or "possible emergency red flag"])

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
        "assistant_reply": (
            "I am concerned this could be an emergency. Call your local emergency number now."
            if emergency_hit
            else extraction.next_question
        ),
    }
    return updated_state
