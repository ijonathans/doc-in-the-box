"""Ask user for consent to check and book an appointment before proceeding to RAG + provider search."""

from typing import Any

from app.graphs.state import InterviewState

BOOKING_CONSENT_MESSAGE = (
    "I can check and book an appointment for you in the nearest clinic, would you like me to do that?"
)


async def ask_booking_consent_node(state: InterviewState) -> dict[str, Any]:
    """
    Stateless: returns only assistant_reply asking for booking consent.
    No other state changes.
    """
    return {"assistant_reply": BOOKING_CONSENT_MESSAGE}
