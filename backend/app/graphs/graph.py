from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.graphs.ask_booking_consent_node import ask_booking_consent_node
from app.graphs.normal_chat_node import normal_chat_node
from app.graphs.nurse_intake_node import nurse_intake_node
from app.graphs.provider_locations_node import provider_locations_node
from app.graphs.rag_medlineplus_node import rag_medlineplus_node
from app.graphs.router_node import router_node
from app.graphs.state import InterviewState
from app.graphs.state_verifier_node import state_verifier_node


class TriageInterviewGraph:
    def __init__(self, model: ChatOpenAI | None) -> None:
        self.model = model
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(InterviewState)

        async def _router_wrapper(state: InterviewState) -> dict[str, Any]:
            return await router_node(state, self.model)

        async def _normal_chat_wrapper(state: InterviewState) -> dict[str, Any]:
            return await normal_chat_node(state, self.model)

        async def _nurse_wrapper(state: InterviewState) -> dict[str, Any]:
            return await nurse_intake_node(state, self.model)

        async def _verifier_wrapper(state: InterviewState) -> dict[str, Any]:
            return await state_verifier_node(state)

        def _route_selector(state: InterviewState) -> str:
            return state.get("route_intent", "normal_chat")

        def _ready_node(state: InterviewState) -> dict[str, Any]:
            return {"next_action": "ready_for_handoff", "assistant_reply": state.get("assistant_reply", "")}

        def _emergency_node(state: InterviewState) -> dict[str, Any]:
            return {"next_action": "emergency_escalation", "assistant_reply": state.get("assistant_reply", "")}

        async def _rag_wrapper(state: InterviewState) -> dict[str, Any]:
            return await rag_medlineplus_node(state, self.model)

        async def _ask_consent_wrapper(state: InterviewState) -> dict[str, Any]:
            return await ask_booking_consent_node(state)

        async def _provider_locations_wrapper(state: InterviewState) -> dict[str, Any]:
            return await provider_locations_node(state)

        def _after_ready_selector(state: InterviewState) -> str:
            if state.get("booking_confirmed"):
                return "rag"
            return "ask_consent"

        workflow.add_node("router_node", _router_wrapper)
        workflow.add_node("normal_chat_node", _normal_chat_wrapper)
        workflow.add_node("nurse_intake_node", _nurse_wrapper)
        workflow.add_node("state_verifier_node", _verifier_wrapper)
        workflow.add_node("ready_for_handoff", _ready_node)
        workflow.add_node("ask_booking_consent_node", _ask_consent_wrapper)
        workflow.add_node("rag_medlineplus_node", _rag_wrapper)
        workflow.add_node("provider_locations_node", _provider_locations_wrapper)
        workflow.add_node("emergency_escalation", _emergency_node)

        workflow.add_edge(START, "router_node")
        workflow.add_conditional_edges(
            "router_node",
            _route_selector,
            {"normal_chat": "normal_chat_node", "triage": "nurse_intake_node"},
        )
        workflow.add_edge("normal_chat_node", END)
        workflow.add_edge("nurse_intake_node", "state_verifier_node")
        workflow.add_conditional_edges(
            "state_verifier_node",
            lambda state: state.get("next_action", "continue_questioning"),
            {
                "continue_questioning": END,
                "ready_for_handoff": "ready_for_handoff",
                "emergency_escalation": "emergency_escalation",
            },
        )
        workflow.add_conditional_edges(
            "ready_for_handoff",
            _after_ready_selector,
            {"rag": "rag_medlineplus_node", "ask_consent": "ask_booking_consent_node"},
        )
        workflow.add_edge("ask_booking_consent_node", END)
        workflow.add_edge("rag_medlineplus_node", "provider_locations_node")
        workflow.add_edge("provider_locations_node", END)
        workflow.add_edge("emergency_escalation", END)
        return workflow.compile()

    async def run(self, state: InterviewState) -> InterviewState:
        return await self.graph.ainvoke(state)
