from openai import OpenAI

from app.core.config import settings


class SymptomTriageService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def summarize_and_classify(
        self,
        symptoms_text: str,
        chronic_conditions: str | None,
        memory_context: str | None = None,
    ) -> dict:
        if not self.client:
            return {
                "symptom_summary": symptoms_text.strip(),
                "urgency_level": "medium",
                "recommended_specialty": "Primary Care",
            }

        prompt = (
            "You are a cautious healthcare intake assistant. "
            "Summarize symptoms, classify urgency (low/medium/high), and propose specialty. "
            "Return strict JSON with keys: symptom_summary, urgency_level, recommended_specialty."
        )
        user_input = (
            f"Symptoms: {symptoms_text}\n"
            f"Chronic conditions: {chronic_conditions or 'none'}\n"
            f"Long-term memory context: {memory_context or 'none'}\n"
            "No diagnosis. Only intake guidance."
        )

        response = self.client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input},
            ],
        )
        text_output = response.output_text

        # Keep parsing simple for initial implementation.
        urgency_level = "medium"
        recommended_specialty = "Primary Care"
        if "high" in text_output.lower():
            urgency_level = "high"
        if "dermatology" in text_output.lower():
            recommended_specialty = "Dermatology"
        elif "cardiology" in text_output.lower():
            recommended_specialty = "Cardiology"

        return {
            "symptom_summary": text_output.strip(),
            "urgency_level": urgency_level,
            "recommended_specialty": recommended_specialty,
        }

