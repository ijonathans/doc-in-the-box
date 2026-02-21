MAJOR_RED_FLAGS = [
    "chest pain",
    "shortness of breath",
    "one-sided weakness",
    "slurred speech",
    "severe bleeding",
    "fainting",
    "confusion",
    "suicidal thoughts",
    "anaphylaxis",
]

HEALTH_INTENT_HINTS = [
    "pain",
    "ache",
    "symptom",
    "sick",
    "ill",
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
