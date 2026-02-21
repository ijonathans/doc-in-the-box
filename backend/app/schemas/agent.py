from pydantic import BaseModel


class SymptomIntakeRequest(BaseModel):
    patient_id: int
    symptoms_text: str
    preferred_zip_code: str


class DoctorMatch(BaseModel):
    doctor_external_id: str
    doctor_name: str
    specialty: str
    location: str
    next_available_slot: str
    accepted_insurance: str


class AgentRecommendation(BaseModel):
    symptom_summary: str
    urgency_level: str
    recommended_specialty: str
    doctor_candidates: list[DoctorMatch]

