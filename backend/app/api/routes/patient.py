from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.schemas.agent import SymptomIntakeRequest
from app.schemas.appointment import AppointmentCreate, AppointmentOut
from app.schemas.patient import PatientCreate, PatientOut
from app.services.ai_agent import ProactiveAIAgentService
from app.services.memory.memory_orchestrator import MemoryOrchestrator
from app.services.scheduler_service import SchedulerService


router = APIRouter()
agent_service = ProactiveAIAgentService()
scheduler_service = SchedulerService()
memory_orchestrator = MemoryOrchestrator()


@router.post("/register", response_model=PatientOut)
async def register_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    await memory_orchestrator.persist_profile_fact(patient)
    return patient


@router.post("/intake")
async def submit_symptoms(payload: SymptomIntakeRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    recommendation = await agent_service.evaluate_and_recommend(
        patient=patient,
        symptoms_text=payload.symptoms_text,
        preferred_zip_code=payload.preferred_zip_code,
    )
    await memory_orchestrator.persist_symptom_visit(
        patient=patient,
        symptoms_text=payload.symptoms_text,
        symptom_summary=recommendation.symptom_summary,
    )
    return recommendation


@router.post("/appointments", response_model=AppointmentOut)
async def book_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    try:
        appointment = await scheduler_service.create_and_confirm_appointment(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return appointment


@router.get("/{patient_id}/appointments", response_model=list[AppointmentOut])
def list_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    return db.query(Appointment).filter(Appointment.patient_id == patient_id).all()

