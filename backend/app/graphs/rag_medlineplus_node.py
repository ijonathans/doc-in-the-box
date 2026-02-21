"""Post-handoff RAG node: MedlinePlus KB search, infer provider type, Zocdoc search, set kb_evidence, provider_search, and assistant_reply."""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.graphs.state import InterviewState
from app.services.kb_medlineplus_service import KBMedlinePlusService
from app.services.zocdoc_client import ZocDocClient

TOP_K = 5
DEFAULT_ZIP = "10001"
INSURANCE_PLACEHOLDER = "Unknown"


class RecommendedProvider(BaseModel):
    """LLM output: single best doctor/clinic type for the patient's complaint and KB evidence."""

    specialty: str = Field(description="Doctor or clinic specialty, e.g. Primary Care, Allergy and Immunology")
    description: str = Field(description="Short patient-facing phrase, e.g. focus on allergies")


def _build_query(state: InterviewState) -> str:
    parts = []
    if state.get("chief_complaint"):
        parts.append(state["chief_complaint"])
    symptoms = state.get("symptoms") or []
    parts.extend(symptoms)
    if state.get("timeline"):
        parts.append(state["timeline"])
    return " ".join(parts).strip()


def _medlineplus_block(kb_evidence: list[dict[str, Any]]) -> str:
    if not kb_evidence:
        return "I don't have specific health topic matches for your symptoms right now. Please discuss your concerns with a health care provider."
    lines = ["Based on your symptoms, here are relevant health topics from MedlinePlus:", ""]
    for item in kb_evidence[:5]:
        title = item.get("title") or "Topic"
        url = item.get("url") or ""
        if url:
            lines.append(f"• {title}: {url}")
        else:
            lines.append(f"• {title}")
    return "\n".join(lines)


def _evidence_context_for_llm(evidence: list[dict[str, Any]], max_items: int = 3, text_len: int = 200) -> str:
    """Build a short context string from top evidence for the LLM."""
    parts = []
    for item in evidence[:max_items]:
        title = item.get("title") or "Topic"
        text = (item.get("text") or "")[:text_len]
        parts.append(f"- {title}: {text}")
    return "\n".join(parts) if parts else "No specific topics found."


async def _infer_recommended_provider(
    state: InterviewState,
    evidence: list[dict[str, Any]],
    model: ChatOpenAI | None,
) -> RecommendedProvider:
    if not model or not evidence:
        return RecommendedProvider(specialty="Primary Care", description="general health concerns")
    complaint = state.get("chief_complaint") or ""
    symptoms = state.get("symptoms") or []
    timeline = state.get("timeline") or ""
    context = _evidence_context_for_llm(evidence)
    prompt = (
        "Given the patient's chief complaint, symptoms, timeline, and the relevant health topics below, "
        "choose the single best doctor or clinic type (specialty) and a short patient-facing description. "
        "Use standard specialty names such as Primary Care, Allergy and Immunology, Dermatology, Cardiology, etc. "
        "Return only one specialty and one short phrase for description (e.g. 'focus on allergies')."
    )
    user_content = (
        f"Chief complaint: {complaint}\n"
        f"Symptoms: {', '.join(symptoms)}\n"
        f"Timeline: {timeline}\n\n"
        f"Relevant health topics:\n{context}"
    )
    try:
        chain = model.with_structured_output(RecommendedProvider)
        result = await chain.ainvoke([{"role": "system", "content": prompt}, {"role": "user", "content": user_content}])
        return result
    except Exception:
        return RecommendedProvider(specialty="Primary Care", description="general health concerns")


def _zip_from_state(state: InterviewState) -> str:
    loc = state.get("patient_context") or {}
    loc = loc.get("location") or {}
    zip_val = loc.get("zip") or ""
    return (zip_val or DEFAULT_ZIP).strip() or DEFAULT_ZIP


def _build_combined_reply(
    kb_evidence: list[dict[str, Any]],
    specialty: str,
    description: str,
    provider_results: list[dict[str, Any]],
) -> str:
    blocks = []
    blocks.append(_medlineplus_block(kb_evidence))
    blocks.append("")
    blocks.append(f"We recommend seeing a **{specialty}** ({description}).")
    if provider_results:
        blocks.append("")
        blocks.append("Here are some options:")
        blocks.append("")
        for doc in provider_results[:5]:
            name = doc.get("doctor_name") or "Provider"
            location = doc.get("location") or ""
            slot = doc.get("next_available_slot") or ""
            if slot:
                blocks.append(f"• {name} — {location} (next: {slot})")
            else:
                blocks.append(f"• {name} — {location}")
    return "\n".join(blocks)


async def rag_medlineplus_node(state: InterviewState, model: ChatOpenAI | None = None) -> dict[str, Any]:
    """
    Run after ready_for_handoff: MedlinePlus KB search, infer provider type, Zocdoc search,
    set kb_evidence, provider_search (constraints + results), and assistant_reply.
    """
    query = _build_query(state)
    kb = KBMedlinePlusService()
    if not kb.is_available or not query:
        return {
            "kb_evidence": [],
            "provider_search": {"constraints": {}, "results": []},
            "assistant_reply": state.get("assistant_reply")
            or "Intake complete. I couldn't search health topics right now; please talk to a provider.",
        }
    results = await kb.search(query, top_k=TOP_K)
    evidence: list[dict[str, Any]] = [
        {"title": r.get("title"), "url": r.get("url"), "text": (r.get("text") or "")[:500], "score": r.get("score")}
        for r in results
    ]

    recommended = await _infer_recommended_provider(state, evidence, model)
    specialty = recommended.specialty or "Primary Care"
    description = recommended.description or "general health concerns"

    zip_code = _zip_from_state(state)
    zocdoc = ZocDocClient()
    try:
        provider_results = await zocdoc.search_doctors(
            zip_code=zip_code,
            specialty=specialty,
            insurance_provider=INSURANCE_PLACEHOLDER,
        )
    except Exception:
        provider_results = []

    constraints: dict[str, Any] = {
        "recommended_specialty": specialty,
        "description": description,
    }
    # Reply: MedlinePlus + recommendation only; provider_locations_node appends clinic list (top 3).
    reply = _build_combined_reply(evidence, specialty, description, [])

    return {
        "kb_evidence": evidence,
        "provider_search": {"constraints": constraints, "results": provider_results},
        "assistant_reply": reply,
    }
