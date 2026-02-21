from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.graphs.normal_chat_node import normal_chat_node
from app.graphs.nurse_intake_node import nurse_intake_node
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

        workflow.add_node("router_node", _router_wrapper)
        workflow.add_node("normal_chat_node", _normal_chat_wrapper)
        workflow.add_node("nurse_intake_node", _nurse_wrapper)
        workflow.add_node("state_verifier_node", _verifier_wrapper)
        workflow.add_node("ready_for_handoff", _ready_node)
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
                "continue_questioning": "nurse_intake_node",
                "ready_for_handoff": "ready_for_handoff",
                "emergency_escalation": "emergency_escalation",
            },
        )
        workflow.add_edge("ready_for_handoff", END)
        workflow.add_edge("emergency_escalation", END)
        return workflow.compile()

    async def run(self, state: InterviewState) -> InterviewState:
        return await self.graph.ainvoke(state)
