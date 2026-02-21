from app.schemas.agent import AgentRecommendation
from app.models.patient import Patient
from app.services.doctor_matching import DoctorMatchingService
from app.services.epic_fhir_client import EpicFhirClient
from app.services.memory.memory_orchestrator import MemoryOrchestrator
from app.services.triage import SymptomTriageService
from app.services.zocdoc_client import ZocDocClient


class ProactiveAIAgentService:
    def __init__(self) -> None:
        self.triage_service = SymptomTriageService()
        self.epic_client = EpicFhirClient()
        self.zocdoc_client = ZocDocClient()
        self.matcher = DoctorMatchingService()
        self.memory_orchestrator = MemoryOrchestrator()

    async def evaluate_and_recommend(
        self,
        patient: Patient,
        symptoms_text: str,
        preferred_zip_code: str,
    ) -> AgentRecommendation:
        health_history = await self.epic_client.get_patient_history(patient.epic_patient_id)
        memory_context = await self.memory_orchestrator.get_triage_context(
            patient=patient,
            symptoms_text=symptoms_text,
            health_history=health_history,
        )
        triage = self.triage_service.summarize_and_classify(
            symptoms_text=symptoms_text,
            chronic_conditions=f"{patient.chronic_conditions or ''}; {health_history.get('conditions', [])}",
            memory_context=memory_context,
        )

        doctors = await self.zocdoc_client.search_doctors(
            zip_code=preferred_zip_code,
            specialty=triage["recommended_specialty"],
            insurance_provider=patient.insurance_provider,
        )
        ranked = self.matcher.rank_candidates(doctors=doctors, urgency_level=triage["urgency_level"])

        return AgentRecommendation(
            symptom_summary=triage["symptom_summary"],
            urgency_level=triage["urgency_level"],
            recommended_specialty=triage["recommended_specialty"],
            doctor_candidates=ranked,
        )

