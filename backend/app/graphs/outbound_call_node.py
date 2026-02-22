"""
After provider_locations: start ElevenLabs outbound call to the next clinic in the top 3.
Call one by one; when a clinic is available and booked (via webhook), do not call the rest.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.graphs.state import InterviewState
from app.services.elevenlabs_call_agent import ElevenLabsCallAgent
from app.services.session_store import RedisSessionStore

# We do not override the system prompt or first message; the agent uses the
# configuration set in the ElevenLabs platform (Doc-in-the-box). We only pass
# dynamic_variables (clinic_name, clinic_address, chief_complaint, patient_first_name)
# so the platform prompt can reference them if needed.


async def outbound_call_node(state: InterviewState) -> dict[str, Any]:
    """
    Start one outbound call to the next clinic in provider_search.results (by outbound_call.next_clinic_index).
    If no credentials or no clinics, return without calling. Call is placed via ElevenLabs + Twilio.
    """
    results = (state.get("provider_search") or {}).get("results") or []
    outbound = state.get("outbound_call") or {}
    next_index = outbound.get("next_clinic_index", 0)

    if next_index >= len(results):
        return {
            "assistant_reply": (
                "We've contacted all the clinics we had. If you didn't get a callback yet, we'll update you when the call completes."
            ),
            "outbound_call": {
                **outbound,
                "next_clinic_index": next_index,
                "call_started": False,
            },
        }
    clinic = results[next_index]
    clinic_name = (clinic.get("doctor_name") or "the clinic").strip()
    phone = clinic.get("phone_number") or ""
    address = clinic.get("address") or ""
    chief_complaint = state.get("chief_complaint") or ""

    call_agent = ElevenLabsCallAgent(
        api_key=settings.elevenlabs_api_key,
        agent_id=settings.elevenlabs_agent_id,
        agent_phone_number_id=settings.elevenlabs_agent_phone_number_id,
    )
    patient_first_name = (state.get("patient_context") or {}).get("first_name", "") or ""
    dynamic_variables = {
        "clinic_name": clinic_name,
        "clinic_address": address,
        "chief_complaint": chief_complaint or "general visit",
        "patient_first_name": patient_first_name,
    }
    # No prompt_override or first_message: use the agent's system prompt and first message from the ElevenLabs platform.
    result = await call_agent.start_twilio_outbound_call(
        phone,
        dynamic_variables=dynamic_variables,
    )

    if result.get("success"):
        conversation_id = result.get("conversation_id", "")
        session_id = state.get("session_id")
        if conversation_id and session_id:
            store = RedisSessionStore()
            await store.set_conversation_session(conversation_id, session_id)
        return {
            "assistant_reply": (
                f"We're calling the clinic ({clinic_name}'s office) now to check availability and book your appointment. "
                "We'll notify you when the call is complete."
            ),
            "outbound_call": {
                **outbound,
                "next_clinic_index": next_index,
                "conversation_id": conversation_id,
                "call_started": True,
                "booking_result": "pending",
                "last_result": result,
            },
        }
    msg = result.get("message", "unknown error")
    hint = ""
    if "Missing" in msg or "missing" in msg.lower():
        hint = " Check that ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID, and ELEVENLABS_AGENT_PHONE_NUMBER_ID are set in your .env (see backend/docs/outbound-call-setup.md)."
    return {
        "assistant_reply": (
            f"We couldn't start the call to {clinic_name} ({phone}). Error: {msg}.{hint} "
            "You can call them directly at the number above, or fix the setup and try again."
        ),
        "outbound_call": {
            **outbound,
            "next_clinic_index": next_index,
            "call_started": False,
            "last_result": result,
        },
    }
