"""Collect patient appointment availability (when they are free), output JSON and formatted string for ElevenLabs."""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.graphs.state import InterviewState

ASK_AVAILABILITY_MESSAGE = (
    "When are you available for an appointment? For example: Monday morning until 10am, Friday 3PM to 6PM."
)


class DayAvailability(BaseModel):
    """Single day with one or more time ranges."""

    day: str = Field(description="Day of week, e.g. Monday, Tuesday, Friday")
    time_ranges: list[str] = Field(
        default_factory=list,
        description="Time ranges that day, e.g. ['morning until 10am'] or ['3PM to 6 PM']",
    )


class AvailabilityExtraction(BaseModel):
    """Structured availability parsed from user message."""

    days: list[DayAvailability] = Field(default_factory=list)


def _format_availability_for_elevenlabs(slots: dict[str, list[str]]) -> str:
    """Turn slots dict into a single string for the voice agent."""
    if not slots:
        return ""
    parts = []
    for day, ranges in slots.items():
        if ranges:
            parts.append(f"{day} {' and '.join(ranges)}")
    return ", ".join(parts)


async def _parse_availability_message(message: str, model: ChatOpenAI | None) -> dict[str, list[str]]:
    """Parse free-text availability into day -> list of time ranges. Returns empty dict on failure."""
    if not message or not message.strip():
        return {}
    if not model:
        # Fallback: treat whole message as one block (e.g. "weekday mornings")
        return {"General": [message.strip()]}
    try:
        chain = model.with_structured_output(AvailabilityExtraction)
        result = await chain.ainvoke(
            [
                (
                    "system",
                    "Extract the person's appointment availability from their message. "
                    "Return each day of the week they mention (Monday, Tuesday, etc.) and the time ranges for that day "
                    "(e.g. 'morning until 10am', '3PM to 6 PM', 'afternoon'). "
                    "If they give a general time without a day, use day 'General'. "
                    "Keep time ranges in their words, short and natural for speaking.",
                ),
                ("user", message),
            ]
        )
        if not result or not result.days:
            return {}
        return {d.day: d.time_ranges for d in result.days if d.day and d.time_ranges}
    except Exception:
        return {"General": [message.strip()]}


async def availability_node(state: InterviewState, model: ChatOpenAI | None = None) -> dict[str, Any]:
    """
    If we already have patient_availability_time, return minimal update (graph routes to RAG).
    If awaiting_availability and user replied, parse message into slots + formatted string, clear awaiting_availability.
    Else ask when they're available and set awaiting_availability=True (graph routes to END).
    """
    existing_time = (state.get("patient_availability_time") or "").strip()
    if existing_time:
        return {}

    awaiting = state.get("awaiting_availability")
    latest_message = (state.get("latest_user_message") or "").strip()

    if awaiting and latest_message:
        slots = await _parse_availability_message(latest_message, model)
        formatted = _format_availability_for_elevenlabs(slots)
        if not formatted:
            formatted = latest_message
        return {
            "patient_availability_slots": slots,
            "patient_availability_time": formatted,
            "awaiting_availability": False,
        }

    return {
        "assistant_reply": ASK_AVAILABILITY_MESSAGE,
        "awaiting_availability": True,
    }
