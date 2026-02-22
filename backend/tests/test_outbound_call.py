"""
Integration test: start one outbound call via ElevenLabs so you can receive a call.
Set OUTBOUND_CALL_TEST_PHONE in .env (E.164, e.g. +15551234567) to run; otherwise the test is skipped.
"""

import pytest

from app.core.config import settings
from app.services.elevenlabs_call_agent import ElevenLabsCallAgent

OUTBOUND_CALL_TEST_PHONE = (settings.outbound_call_test_phone or "").strip()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_outbound_call_receive_from_elevenlabs() -> None:
    """
    Start one outbound call to OUTBOUND_CALL_TEST_PHONE using .env-configured agent.
    When the env var is set, your phone should ring; the test asserts the API reports success.
    """
    if not OUTBOUND_CALL_TEST_PHONE:
        pytest.skip("Set OUTBOUND_CALL_TEST_PHONE to receive a call (e.g. in .env)")

    call_agent = ElevenLabsCallAgent(
        api_key=settings.elevenlabs_api_key,
        agent_id=settings.elevenlabs_agent_id,
        agent_phone_number_id=settings.elevenlabs_agent_phone_number_id,
    )
    result = await call_agent.start_twilio_outbound_call(
        OUTBOUND_CALL_TEST_PHONE,
        first_message="Hi, this is a quick test call. You can hang up anytime.",
    )

    assert result.get("success") is True, result.get("message", "unknown error")
    assert result.get("conversation_id"), "expected conversation_id when call was started"
