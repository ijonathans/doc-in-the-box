from unittest.mock import AsyncMock, patch

import pytest

from app.graphs.ask_booking_consent_node import ask_booking_consent_node, BOOKING_CONSENT_MESSAGE

# Run with -s to see chat text in logs: pytest tests/test_langgraph_triage.py -s


def _log_chat(test_name: str, user: str | None, assistant: str | None) -> None:
    if user is not None:
        print(f"\n[{test_name}] user: {user}")
    if assistant is not None:
        print(f"[{test_name}] assistant: {assistant}")
from app.graphs.graph import TriageInterviewGraph
from app.graphs.normal_chat_node import normal_chat_node
from app.graphs.nurse_intake_node import nurse_intake_node
from app.graphs.provider_locations_node import provider_locations_node
from app.graphs.rag_medlineplus_node import rag_medlineplus_node
from app.graphs.router_node import router_node
from app.graphs.state import create_default_interview_state
from app.graphs.state_verifier_node import state_verifier_node
from app.services.session_store import RedisSessionStore


@pytest.mark.asyncio
async def test_nurse_node_escalates_on_major_red_flag():
    state = create_default_interview_state("session-1")
    state["latest_user_message"] = "I have severe chest pain and I feel like passing out."

    updated = await nurse_intake_node(state, model=None)
    _log_chat("test_nurse_node_escalates_on_major_red_flag", state["latest_user_message"], updated.get("assistant_reply"))

    assert updated["needs_emergency"] is True
    assert "emergency" in updated["assistant_reply"].lower()


@pytest.mark.asyncio
async def test_verifier_requires_minimum_dataset():
    state = create_default_interview_state("session-2")
    state["red_flags"] = {"present": [], "absent": ["chest pain"], "unknown": []}

    verified = await state_verifier_node(state)
    _log_chat("test_verifier_requires_minimum_dataset", None, verified.get("assistant_reply"))

    assert verified["handoff_ready"] is False
    assert verified["next_action"] == "continue_questioning"
    assert "chief_complaint" in verified["missing_fields"]
    assert "timeline" in verified["missing_fields"]


@pytest.mark.asyncio
async def test_verifier_marks_handoff_ready_when_complete():
    state = create_default_interview_state("session-3")
    state["chief_complaint"] = "Persistent cough"
    state["timeline"] = "Started 3 days ago"
    state["red_flags"] = {
        "present": [],
        "absent": ["chest pain", "shortness of breath", "fainting", "confusion"],
        "unknown": [],
    }

    verified = await state_verifier_node(state)
    _log_chat("test_verifier_marks_handoff_ready_when_complete", None, verified.get("assistant_reply"))

    assert verified["handoff_ready"] is True
    assert verified["next_action"] == "ready_for_handoff"
    assert verified["missing_fields"] == []


@pytest.mark.asyncio
async def test_verifier_emergency_override():
    state = create_default_interview_state("session-emergency-override")
    state["needs_emergency"] = True
    state["assistant_reply"] = "Emergency detected."

    verified = await state_verifier_node(state)
    _log_chat("test_verifier_emergency_override", None, verified.get("assistant_reply"))

    assert verified["next_action"] == "emergency_escalation"
    assert verified["needs_emergency"] is True
    assert verified["handoff_ready"] is False


@pytest.mark.asyncio
async def test_verifier_only_timeline_missing():
    state = create_default_interview_state("session-timeline-missing")
    state["chief_complaint"] = "Headache"

    verified = await state_verifier_node(state)
    _log_chat("test_verifier_only_timeline_missing", None, verified.get("assistant_reply"))

    assert verified["next_action"] == "continue_questioning"
    assert verified["missing_fields"] == ["timeline"]


@pytest.mark.asyncio
async def test_router_routes_normal_message_to_normal_chat():
    state = create_default_interview_state("session-router-normal")
    state["latest_user_message"] = "Tell me a fun fact about space."

    routed = await router_node(state, model=None)
    _log_chat("test_router_routes_normal_message_to_normal_chat", state["latest_user_message"], None)

    assert routed["route_intent"] == "normal_chat"
    assert routed["conversation_mode"] == "normal_chat"


@pytest.mark.asyncio
async def test_router_routes_health_message_to_triage():
    state = create_default_interview_state("session-router-triage")
    state["latest_user_message"] = "I have chest pain and shortness of breath."

    routed = await router_node(state, model=None)
    _log_chat("test_router_routes_health_message_to_triage", state["latest_user_message"], None)

    assert routed["route_intent"] == "triage"
    assert routed["conversation_mode"] == "triage"


@pytest.mark.asyncio
async def test_router_keeps_sticky_triage_mode():
    state = create_default_interview_state("session-router-sticky")
    state["conversation_mode"] = "triage"
    state["latest_user_message"] = "what is the weather today?"

    routed = await router_node(state, model=None)
    _log_chat("test_router_keeps_sticky_triage_mode", state["latest_user_message"], None)

    assert routed["route_intent"] == "triage"
    assert routed["conversation_mode"] == "triage"


@pytest.mark.asyncio
async def test_normal_chat_node_returns_response():
    state = create_default_interview_state("session-normal-node")
    state["latest_user_message"] = "Hello there!"

    updated = await normal_chat_node(state, model=None)
    _log_chat("test_normal_chat_node_returns_response", state["latest_user_message"], updated.get("assistant_reply"))

    assert updated["route_intent"] == "normal_chat"
    assert updated["assistant_reply"]


@pytest.mark.asyncio
async def test_graph_routes_end_to_end_for_normal_chat():
    graph = TriageInterviewGraph(model=None)
    state = create_default_interview_state("session-graph-normal")
    state["latest_user_message"] = "Can you recommend a productivity tip?"

    updated = await graph.run(state)
    _log_chat("test_graph_routes_end_to_end_for_normal_chat", state["latest_user_message"], updated.get("assistant_reply"))

    assert updated["route_intent"] == "normal_chat"
    assert updated["conversation_mode"] == "normal_chat"
    assert updated["assistant_reply"]


@pytest.mark.asyncio
async def test_graph_sticky_triage_across_turns():
    graph = TriageInterviewGraph(model=None)
    state = create_default_interview_state("session-graph-sticky")
    state["conversation_mode"] = "triage"
    state["route_intent"] = "triage"
    state["chief_complaint"] = "Headache"
    state["timeline"] = "Started yesterday"
    state["latest_user_message"] = "I have a severe headache and feel dizzy."

    first_turn = await graph.run(state)
    _log_chat("test_graph_sticky_triage (turn 1)", state["latest_user_message"], first_turn.get("assistant_reply"))
    assert first_turn["conversation_mode"] == "triage"

    first_turn["latest_user_message"] = "Actually, can you tell me a joke?"
    second_turn = await graph.run(first_turn)
    _log_chat("test_graph_sticky_triage (turn 2)", first_turn["latest_user_message"], second_turn.get("assistant_reply"))
    assert second_turn["conversation_mode"] == "triage"
    assert second_turn["route_intent"] == "triage"


class _FakeRedis:
    def __init__(self):
        self.data: dict[str, str] = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def setex(self, key: str, _ttl: int, payload: str):
        self.data[key] = payload


@pytest.mark.asyncio
async def test_rag_medlineplus_node_populates_kb_evidence_and_reply():
    state = create_default_interview_state("session-rag")
    state["chief_complaint"] = "Headache"
    state["timeline"] = "Started yesterday"
    state["symptoms"] = ["dizzy"]

    mock_results = [
        {"title": "Headache", "url": "https://medlineplus.gov/headache.html", "text": "Summary...", "score": 0.9},
    ]
    with patch("app.graphs.rag_medlineplus_node.KBMedlinePlusService") as MockKB:
        instance = MockKB.return_value
        instance.is_available = True
        instance.search = AsyncMock(return_value=mock_results)
        updated = await rag_medlineplus_node(state)

    _log_chat("test_rag_medlineplus_node_populates_kb_evidence_and_reply", None, updated.get("assistant_reply"))
    assert updated["kb_evidence"]
    assert updated["kb_evidence"][0].get("title") == "Headache"
    assert updated["assistant_reply"]
    assert "Headache" in updated["assistant_reply"]
    assert "medlineplus.gov" in updated["assistant_reply"]


@pytest.mark.asyncio
async def test_rag_medlineplus_node_provider_search_and_reply():
    """RAG returns provider_search (constraints + results); reply is MedlinePlus + recommendation only (clinic list added by provider_locations_node)."""
    state = create_default_interview_state("session-rag-zocdoc")
    state["chief_complaint"] = "Rash on arm"
    state["timeline"] = "Since last week"
    state["symptoms"] = ["itching"]
    state["patient_context"] = {"location": {"zip": "10001", "state": "NY", "country": "US"}}

    mock_kb_results = [
        {"title": "Rash", "url": "https://medlineplus.gov/rash.html", "text": "Skin rash...", "score": 0.9},
    ]
    mock_doctors = [
        {"doctor_name": "Dr. Jane Smith", "specialty": "Dermatology", "location": "10001 - Skin Care", "next_available_slot": "2026-02-24T09:00:00"},
        {"doctor_name": "Dr. John Doe", "specialty": "Dermatology", "location": "10002 - Downtown", "next_available_slot": ""},
    ]
    with patch("app.graphs.rag_medlineplus_node.KBMedlinePlusService") as MockKB, patch(
        "app.graphs.rag_medlineplus_node.ZocDocClient"
    ) as MockZocdoc:
        MockKB.return_value.is_available = True
        MockKB.return_value.search = AsyncMock(return_value=mock_kb_results)
        MockZocdoc.return_value.search_doctors = AsyncMock(return_value=mock_doctors)
        updated = await rag_medlineplus_node(state, model=None)

    assert "provider_search" in updated
    constraints = updated["provider_search"]["constraints"]
    assert "recommended_specialty" in constraints
    assert "description" in constraints
    assert constraints["recommended_specialty"]
    assert constraints["description"]

    results = updated["provider_search"]["results"]
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0].get("doctor_name") == "Dr. Jane Smith"

    reply = updated["assistant_reply"]
    _log_chat("test_rag_medlineplus_node_provider_search_and_reply", None, reply)
    assert constraints["recommended_specialty"] in reply
    assert constraints["description"] in reply
    # RAG no longer adds provider list to reply; provider_locations_node appends clinic details
    assert "MedlinePlus" in reply or "Rash" in reply


@pytest.mark.asyncio
async def test_ask_booking_consent_node_returns_consent_message():
    state = create_default_interview_state("session-consent")
    state["chief_complaint"] = "Dizzy"
    state["timeline"] = "Yesterday morning"
    out = await ask_booking_consent_node(state)
    _log_chat("test_ask_booking_consent_node_returns_consent_message", None, out.get("assistant_reply"))
    assert out["assistant_reply"] == BOOKING_CONSENT_MESSAGE


@pytest.mark.asyncio
async def test_provider_locations_node_appends_clinic_details():
    state = create_default_interview_state("session-prov")
    state["assistant_reply"] = "We recommend seeing a **Primary Care** (general health)."
    state["provider_search"] = {
        "constraints": {"recommended_specialty": "Primary Care", "description": "general health"},
        "results": [],
    }
    with patch("app.graphs.provider_locations_node.ZocDocClient") as MockZoc:
        MockZoc.return_value.get_provider_locations = AsyncMock(
            return_value=[
                {"doctor_name": "Dr. Alpha", "phone_number": "555-0001", "address": "1 Main St"},
                {"doctor_name": "Dr. Beta", "phone_number": "555-0002", "address": "2 Oak Ave"},
            ]
        )
        updated = await provider_locations_node(state)
    _log_chat("test_provider_locations_node_appends_clinic_details", None, updated.get("assistant_reply"))
    assert "provider_search" in updated
    assert len(updated["provider_search"]["results"]) == 2
    assert updated["provider_search"]["results"][0]["doctor_name"] == "Dr. Alpha"
    assert "Dr. Alpha" in updated["assistant_reply"]
    assert "555-0001" in updated["assistant_reply"]
    assert "3 clinics near you" in updated["assistant_reply"]


@pytest.mark.asyncio
async def test_redis_session_store_round_trip():
    fake_redis = _FakeRedis()
    store = RedisSessionStore(redis_client=fake_redis, ttl_seconds=60)

    state = create_default_interview_state("session-4")
    state["chief_complaint"] = "Headache"
    await store.set("session-4", state)

    loaded = await store.get("session-4")
    assert loaded is not None
    assert loaded["chief_complaint"] == "Headache"
