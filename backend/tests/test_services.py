import pytest

from app.models.patient import Patient
from app.services.ai_agent import ProactiveAIAgentService
from app.services.doctor_matching import DoctorMatchingService
from app.services.epic_fhir_client import EpicFhirClient
from app.services.elevenlabs_call_agent import ElevenLabsCallAgent
from app.services.memory.memory_orchestrator import MemoryOrchestrator
from app.services.sms_service import SmsService
from app.services.triage import SymptomTriageService
from app.services.zocdoc_client import ZocDocClient


def test_triage_fallback():
    service = SymptomTriageService()
    payload = service.summarize_and_classify("I have headache and fatigue", "asthma")
    assert payload["urgency_level"] in {"low", "medium", "high"}
    assert payload["recommended_specialty"]


@pytest.mark.asyncio
async def test_zocdoc_fallback():
    client = ZocDocClient()
    results = await client.search_doctors(zip_code="10001", specialty="Primary Care", insurance_provider="Aetna")
    assert len(results) >= 1
    assert "doctor_name" in results[0]


@pytest.mark.asyncio
async def test_epic_fallback():
    client = EpicFhirClient()
    history = await client.get_patient_history(epic_patient_id=None)
    assert "conditions" in history


def test_doctor_matching():
    matcher = DoctorMatchingService()
    doctors = [
        {"doctor_name": "A", "next_available_slot": "2026-02-25T08:00:00"},
        {"doctor_name": "B", "next_available_slot": "2026-02-21T08:00:00"},
    ]
    ranked = matcher.rank_candidates(doctors, urgency_level="high")
    assert ranked[0]["doctor_name"] == "B"


@pytest.mark.asyncio
async def test_ai_agent_end_to_end():
    service = ProactiveAIAgentService()
    patient = Patient(
        id=1,
        first_name="A",
        last_name="B",
        phone_number="+15550009999",
        insurance_provider="Aetna",
        insurance_member_id="MEM-1",
        epic_patient_id=None,
        chronic_conditions=None,
    )
    recommendation = await service.evaluate_and_recommend(
        patient=patient,
        symptoms_text="mild skin rash for two days",
        preferred_zip_code="10001",
    )
    assert recommendation.recommended_specialty
    assert len(recommendation.doctor_candidates) >= 1


@pytest.mark.asyncio
async def test_elevenlabs_mock():
    call_agent = ElevenLabsCallAgent()
    result = await call_agent.verify_and_book(
        {"doctor_name": "Dr. X", "appointment_time": "2026-02-23T10:00:00", "insurance_provider": "Aetna"}
    )
    assert "call_status" in result


def test_sms_mock():
    sms = SmsService()
    result = sms.send_appointment_confirmation("+15550001111", "Test message")
    assert "status" in result


@pytest.mark.asyncio
async def test_memory_orchestrator_in_memory_mode():
    orchestrator = MemoryOrchestrator()
    patient = Patient(
        id=99,
        first_name="Memory",
        last_name="User",
        phone_number="+15550000099",
        insurance_provider="Aetna",
        insurance_member_id="MEM-99",
        chronic_conditions="asthma",
    )
    await orchestrator.persist_profile_fact(patient)
    await orchestrator.persist_symptom_visit(patient, "headache", "patient has headache")
    memories = await orchestrator.list_patient_memories(patient_id=99, limit=10)
    assert len(memories) >= 2

