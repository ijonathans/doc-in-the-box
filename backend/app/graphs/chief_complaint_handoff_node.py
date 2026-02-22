"""AI node: turn raw chief complaint (patient's own words) into a short handoff phrase for call/RAG."""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.graphs.state import InterviewState


class HandoffPhrase(BaseModel):
    """Single short phrase for handoff to clinic/call agent."""

    handoff_phrase: str = Field(description="Concise phrase, e.g. 'stomach feeling not good' or 'headache'")


async def chief_complaint_handoff_node(
    state: InterviewState, model: ChatOpenAI | None
) -> dict[str, Any]:
    """
    Generate a short handoff phrase from chief_complaint for use in outbound call and RAG.
    Runs only when handoff_ready; downstream nodes use chief_complaint_handoff with fallback to chief_complaint.
    """
    complaint = (state.get("chief_complaint") or "").strip()
    if not complaint:
        return {"chief_complaint_handoff": state.get("chief_complaint") or ""}
    if not model:
        return {"chief_complaint_handoff": complaint}

    body_location = (state.get("body_location") or "").strip()
    symptoms = state.get("symptoms") or []
    context_parts = [f"Chief complaint (patient's words): {complaint}"]
    if body_location:
        context_parts.append(f"Body location: {body_location}")
    if symptoms:
        context_parts.append(f"Symptoms: {', '.join(symptoms[:5])}")

    chain = model.with_structured_output(HandoffPhrase)
    result = await chain.ainvoke(
        [
            (
                "system",
                "You produce a single short phrase for handoff to a clinic or call agent. "
                "Given the patient's chief complaint in their own words, output one concise phrase. "
                "Examples: 'not feeling too well in my stomach' -> 'stomach feeling not good'; "
                "'I have this really bad headache since yesterday' -> 'headache'; "
                "'my throat has been sore and it hurts to swallow' -> 'sore throat'. "
                "Keep it brief (a few words). Do not diagnose; use patient-safe wording. "
                "Return only the handoff_phrase, no other text.",
            ),
            ("user", "\n".join(context_parts)),
        ]
    )
    phrase = (result.handoff_phrase or "").strip() or complaint
    return {"chief_complaint_handoff": phrase}
