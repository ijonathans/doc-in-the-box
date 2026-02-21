import pytest

from app.graphs.graph import TriageInterviewGraph
from app.graphs.normal_chat_node import normal_chat_node
from app.graphs.nurse_intake_node import nurse_intake_node
from app.graphs.router_node import router_node
from app.graphs.state import create_default_interview_state
from app.graphs.state_verifier_node import state_verifier_node
from app.services.session_store import RedisSessionStore


@pytest.mark.asyncio
async def test_nurse_node_escalates_on_major_red_flag():
    state = create_default_interview_state("session-1")
    state["latest_user_message"] = "I have severe chest pain and I feel like passing out."

    updated = await nurse_intake_node(state, model=None)

    assert updated["needs_emergency"] is True
    assert "emergency" in updated["assistant_reply"].lower()


@pytest.mark.asyncio
async def test_verifier_requires_minimum_dataset():
    state = create_default_interview_state("session-2")
    state["red_flags"] = {"present": [], "absent": ["chest pain"], "unknown": []}

    verified = await state_verifier_node(state)

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

    assert verified["handoff_ready"] is True
    assert verified["next_action"] == "ready_for_handoff"
    assert verified["missing_fields"] == []


@pytest.mark.asyncio
async def test_verifier_emergency_override():
    state = create_default_interview_state("session-emergency-override")
    state["needs_emergency"] = True
    state["assistant_reply"] = "Emergency detected."

    verified = await state_verifier_node(state)

    assert verified["next_action"] == "emergency_escalation"
    assert verified["needs_emergency"] is True
    assert verified["handoff_ready"] is False


@pytest.mark.asyncio
async def test_verifier_only_timeline_missing():
    state = create_default_interview_state("session-timeline-missing")
    state["chief_complaint"] = "Headache"

    verified = await state_verifier_node(state)

    assert verified["next_action"] == "continue_questioning"
    assert verified["missing_fields"] == ["timeline"]


@pytest.mark.asyncio
async def test_router_routes_normal_message_to_normal_chat():
    state = create_default_interview_state("session-router-normal")
    state["latest_user_message"] = "Tell me a fun fact about space."

    routed = await router_node(state, model=None)

    assert routed["route_intent"] == "normal_chat"
    assert routed["conversation_mode"] == "normal_chat"


@pytest.mark.asyncio
async def test_router_routes_health_message_to_triage():
    state = create_default_interview_state("session-router-triage")
    state["latest_user_message"] = "I have chest pain and shortness of breath."

    routed = await router_node(state, model=None)

    assert routed["route_intent"] == "triage"
    assert routed["conversation_mode"] == "triage"


@pytest.mark.asyncio
async def test_router_keeps_sticky_triage_mode():
    state = create_default_interview_state("session-router-sticky")
    state["conversation_mode"] = "triage"
    state["latest_user_message"] = "what is the weather today?"

    routed = await router_node(state, model=None)

    assert routed["route_intent"] == "triage"
    assert routed["conversation_mode"] == "triage"


@pytest.mark.asyncio
async def test_normal_chat_node_returns_response():
    state = create_default_interview_state("session-normal-node")
    state["latest_user_message"] = "Hello there!"

    updated = await normal_chat_node(state, model=None)

    assert updated["route_intent"] == "normal_chat"
    assert updated["assistant_reply"]


@pytest.mark.asyncio
async def test_graph_routes_end_to_end_for_normal_chat():
    graph = TriageInterviewGraph(model=None)
    state = create_default_interview_state("session-graph-normal")
    state["latest_user_message"] = "Can you recommend a productivity tip?"

    updated = await graph.run(state)

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
    assert first_turn["conversation_mode"] == "triage"

    first_turn["latest_user_message"] = "Actually, can you tell me a joke?"
    second_turn = await graph.run(first_turn)
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
async def test_redis_session_store_round_trip():
    fake_redis = _FakeRedis()
    store = RedisSessionStore(redis_client=fake_redis, ttl_seconds=60)

    state = create_default_interview_state("session-4")
    state["chief_complaint"] = "Headache"
    await store.set("session-4", state)

    loaded = await store.get("session-4")
    assert loaded is not None
    assert loaded["chief_complaint"] == "Headache"
