import pytest

from app.api.routes.admin import get_metrics, list_patient_memory, reindex_patient_memory
from app.api.routes.patient import book_appointment, register_patient, submit_symptoms
from app.schemas.agent import SymptomIntakeRequest
from app.schemas.appointment import AppointmentCreate
from app.schemas.patient import PatientCreate


@pytest.mark.asyncio
async def test_register_patient(db_session):
    patient = await register_patient(
        PatientCreate(
            first_name="Test",
            last_name="User",
            phone_number="+15550001234",
            insurance_provider="Aetna",
            insurance_member_id="MEM-999",
            chronic_conditions="asthma",
        ),
        db=db_session,
    )
    assert patient.id is not None


@pytest.mark.asyncio
async def test_submit_symptoms(db_session):
    patient = await register_patient(
        PatientCreate(
            first_name="Ana",
            last_name="Lee",
            phone_number="+15550001235",
            insurance_provider="Aetna",
            insurance_member_id="MEM-111",
        ),
        db=db_session,
    )
    result = await submit_symptoms(
        SymptomIntakeRequest(patient_id=patient.id, symptoms_text="chest discomfort", preferred_zip_code="10001"),
        db=db_session,
    )
    assert result.urgency_level in {"low", "medium", "high"}


@pytest.mark.asyncio
async def test_book_appointment(db_session):
    patient = await register_patient(
        PatientCreate(
            first_name="Kim",
            last_name="Tran",
            phone_number="+15550001236",
            insurance_provider="Aetna",
            insurance_member_id="MEM-112",
        ),
        db=db_session,
    )
    appointment = await book_appointment(
        AppointmentCreate(
            patient_id=patient.id,
            doctor_external_id="doc_1001",
            doctor_name="Dr. Sarah Lin",
            specialty="Primary Care",
            appointment_time="2026-02-24T09:00:00",
            clinic_location="10001 - Downtown Clinic",
            symptoms_summary="headache and nausea",
        ),
        db=db_session,
    )
    assert appointment.id is not None
    assert appointment.status in {"booked", "verification_failed"}


def test_admin_metrics(db_session):
    metrics = get_metrics(db=db_session)
    assert "patients" in metrics
    assert "appointments_total" in metrics
    assert "appointments_booked" in metrics


@pytest.mark.asyncio
async def test_admin_memory_endpoints(db_session):
    patient = await register_patient(
        PatientCreate(
            first_name="Memory",
            last_name="Test",
            phone_number="+15550002222",
            insurance_provider="Aetna",
            insurance_member_id="MEM-222",
        ),
        db=db_session,
    )
    listing = await list_patient_memory(patient_id=patient.id, limit=20)
    assert listing["patient_id"] == patient.id
    assert listing["count"] >= 1

    reindex = await reindex_patient_memory(patient_id=patient.id, db=db_session)
    assert reindex["patient_id"] == patient.id

