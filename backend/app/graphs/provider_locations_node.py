"""After RAG: fetch top 3 provider locations (zip 30332), set results and append clinic details to assistant_reply."""

from __future__ import annotations

from typing import Any

from app.graphs.state import InterviewState
from app.services.zocdoc_client import ZocDocClient, DEFAULT_VISIT_REASON_ID, TOP_N_PROVIDERS

HARDCODED_ZIP = "30332"


def _visit_reason_id_from_specialty(specialty: str) -> str:
    """Map recommended_specialty to Zocdoc visit_reason_id. For now use default."""
    # Optional: expand with mapping e.g. {"Primary Care": "pc_...", "Dermatology": "pc_..."}
    return DEFAULT_VISIT_REASON_ID


def _format_clinic_section(results: list[dict[str, Any]]) -> str:
    if not results:
        return ""
    lines = ["", "Here are 3 clinics near you:", ""]
    for r in results:
        name = r.get("doctor_name") or "Provider"
        phone = r.get("phone_number") or ""
        address = r.get("address") or ""
        if phone and address:
            lines.append(f"• {name} — {address} — Phone: {phone}")
        elif address:
            lines.append(f"• {name} — {address}")
        else:
            lines.append(f"• {name}")
    return "\n".join(lines)


async def provider_locations_node(state: InterviewState) -> dict[str, Any]:
    """
    Use hardcoded zip 30332 and provider_search.constraints.recommended_specialty.
    Call Zocdoc get_provider_locations, keep top 3, set provider_search.results and append clinic details to reply.
    """
    constraints = (state.get("provider_search") or {}).get("constraints") or {}
    specialty = (constraints.get("recommended_specialty") or "").strip() or "Primary Care"
    visit_reason_id = _visit_reason_id_from_specialty(specialty)

    client = ZocDocClient()
    try:
        results = await client.get_provider_locations(
            HARDCODED_ZIP,
            visit_reason_id=visit_reason_id,
            page_size=TOP_N_PROVIDERS,
        )
    except Exception:
        results = []

    results = results[:TOP_N_PROVIDERS]
    existing_reply = state.get("assistant_reply") or ""
    clinic_block = _format_clinic_section(results)
    new_reply = (existing_reply.rstrip() + clinic_block) if clinic_block else existing_reply

    current_ps = state.get("provider_search") or {"constraints": {}, "results": []}
    return {
        "provider_search": {
            "constraints": {**current_ps.get("constraints", {}), **constraints},
            "results": results,
        },
        "assistant_reply": new_reply,
    }
