from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings


class TriageOutput(BaseModel):
    """Structured triage result from the LLM."""

    symptom_summary: str = Field(description="Brief summary of the patient's symptoms")
    urgency_level: str = Field(description="One of: low, medium, high")
    recommended_specialty: str = Field(description="Suggested specialty, e.g. Primary Care, Dermatology, Cardiology")


class SymptomTriageService:
    def __init__(self) -> None:
        self.model = (
            ChatGoogleGenerativeAI(model=settings.gemini_model, api_key=settings.gemini_api_key)
            if settings.gemini_api_key
            else None
        )

    def summarize_and_classify(
        self,
        symptoms_text: str,
        chronic_conditions: str | None,
        memory_context: str | None = None,
    ) -> dict:
        if not self.model:
            return {
                "symptom_summary": symptoms_text.strip(),
                "urgency_level": "medium",
                "recommended_specialty": "Primary Care",
            }

        prompt = (
            "You are a cautious healthcare intake assistant. "
            "Summarize symptoms, classify urgency (low/medium/high), and propose specialty. "
            "Return strict JSON with keys: symptom_summary, urgency_level, recommended_specialty. "
            "No diagnosis. Only intake guidance."
        )
        user_input = (
            f"Symptoms: {symptoms_text}\n"
            f"Chronic conditions: {chronic_conditions or 'none'}\n"
            f"Long-term memory context: {memory_context or 'none'}\n"
        )

        chain = self.model.with_structured_output(TriageOutput)
        result = chain.invoke(
            [
                ("system", prompt),
                ("user", user_input),
            ]
        )

        return {
            "symptom_summary": result.symptom_summary.strip(),
            "urgency_level": result.urgency_level.strip().lower() or "medium",
            "recommended_specialty": result.recommended_specialty.strip() or "Primary Care",
        }
