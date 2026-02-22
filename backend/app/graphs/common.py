MAJOR_RED_FLAGS = [
    "trouble breathing",
    "shortness of breath",
    "chest pain",
    "chest pressure",
    "confusion",
    "fainting",
    "hard to wake",
    "severe bleeding",
    "sudden weakness",
    "numbness",
    "facial droop",
    "trouble speaking",
    "slurred speech",
    "one-sided weakness",
    "very high fever",
    "severe pain",
    "dehydration",
    "thoughts of harming",
    "harm yourself",
    "harm others",
    "suicidal thoughts",
    "anaphylaxis",
]

HEALTH_INTENT_HINTS = [
    "pain",
    "ache",
    "symptom",
    "sick",
    "ill",
    "unwell",
    "feeling",
    "fever",
    "cough",
    "vomit",
    "nausea",
    "dizzy",
    "headache",
    "rash",
    "breathing",
]


def dedupe(existing: list[str], incoming: list[str]) -> list[str]:
    merged = [item.strip() for item in existing if item and item.strip()]
    for item in incoming:
        normalized = item.strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def looks_like_emergency(message: str) -> bool:
    lowered = message.lower()
    return any(flag in lowered for flag in MAJOR_RED_FLAGS)


def looks_like_health_concern(message: str) -> bool:
    lowered = message.lower()
    return any(hint in lowered for hint in HEALTH_INTENT_HINTS) or looks_like_emergency(lowered)
