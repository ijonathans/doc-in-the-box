class DoctorMatchingService:
    def rank_candidates(self, doctors: list[dict], urgency_level: str) -> list[dict]:
        ranked = sorted(doctors, key=lambda d: d.get("next_available_slot", ""))
        if urgency_level == "high":
            return ranked[:1] + ranked[1:3]
        return ranked[:3]

