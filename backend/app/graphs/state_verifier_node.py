from typing import Any

from app.graphs.state import InterviewState


def _build_follow_up_question(missing_fields: list[str]) -> str:
    if not missing_fields:
        return "Please share any other important symptom details."
    mapping = {
        "chief_complaint": "What is the main problem you need help with today?",
        "timeline": "When did this start, and has it been constant or changing?",
    }
    return mapping.get(missing_fields[0], "Could you tell me more?")


async def state_verifier_node(state: InterviewState) -> dict[str, Any]:
    red_flags = state.get("red_flags") or {"present": [], "absent": [], "unknown": []}
    missing_fields: list[str] = []

    # Emergency override takes precedence over all completeness checks.
    needs_emergency = bool(state.get("needs_emergency"))
    if needs_emergency:
        return {
            "red_flags": red_flags,
            "needs_emergency": True,
            "handoff_ready": False,
            "missing_fields": missing_fields,
            "next_action": "emergency_escalation",
            "assistant_reply": state.get("assistant_reply")
            or "I am concerned this could be an emergency. Call your local emergency number now.",
        }

    # Minimal required intake dataset for handoff. Timeline must be explicitly given (reject vague inferred values).
    _complaint = (state.get("chief_complaint") or "").strip()
    _timeline = (state.get("timeline") or "").strip()
    vague_timelines = ("today", "recently", "recent", "just started", "lately")
    timeline_insufficient = not _timeline or _timeline.lower() in vague_timelines or len(_timeline) < 4

    if not _complaint:
        missing_fields.append("chief_complaint")
    if timeline_insufficient:
        missing_fields.append("timeline")

    if missing_fields:
        out: dict[str, Any] = {
            "red_flags": red_flags,
            "needs_emergency": False,
            "handoff_ready": False,
            "missing_fields": missing_fields,
            "next_action": "continue_questioning",
            "assistant_reply": state.get("assistant_reply") or _build_follow_up_question(missing_fields),
        }
        if timeline_insufficient and "timeline" in missing_fields:
            out["timeline"] = None  # Clear vague timeline so nurse asks again
        return out

    return {
        "red_flags": red_flags,
        "needs_emergency": False,
        "handoff_ready": True,
        "missing_fields": [],
        "next_action": "ready_for_handoff",
        "assistant_reply": state.get("assistant_reply")
        or "Thanks. I have enough intake details and can proceed with triage reasoning.",
    }
