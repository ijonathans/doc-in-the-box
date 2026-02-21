from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.interaction_log import InteractionLog
from app.models.patient import Patient
from app.services.memory.memory_orchestrator import MemoryOrchestrator


router = APIRouter()
memory_orchestrator = MemoryOrchestrator()


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)) -> dict:
    patient_count = db.query(Patient).count()
    appointment_count = db.query(Appointment).count()
    booked_count = db.query(Appointment).filter(Appointment.status == "booked").count()
    return {
        "patients": patient_count,
        "appointments_total": appointment_count,
        "appointments_booked": booked_count,
    }


@router.get("/appointments")
def list_appointments(db: Session = Depends(get_db)) -> list[dict]:
    items = db.query(Appointment).all()
    return [
        {
            "id": item.id,
            "patient_id": item.patient_id,
            "doctor_name": item.doctor_name,
            "status": item.status,
            "appointment_time": item.appointment_time,
            "insurance_verified": item.insurance_verified,
        }
        for item in items
    ]


@router.get("/interactions")
def list_interactions(db: Session = Depends(get_db)) -> list[dict]:
    items = db.query(InteractionLog).order_by(InteractionLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": item.id,
            "patient_id": item.patient_id,
            "interaction_type": item.interaction_type,
            "channel": item.channel,
            "status": item.status,
            "content": item.content,
        }
        for item in items
    ]


@router.get("/memory/{patient_id}")
async def list_patient_memory(patient_id: int, limit: int = 20) -> dict:
    memories = await memory_orchestrator.list_patient_memories(patient_id=patient_id, limit=limit)
    redacted = []
    for item in memories:
        redacted.append(
            {
                "memory_id": item.get("memory_id"),
                "memory_type": item.get("memory_type"),
                "patient_id": item.get("patient_id"),
                "created_at": item.get("created_at"),
                "metadata": item.get("metadata", {}),
                "text_preview": (item.get("text", "")[:140]),
            }
        )
    return {"patient_id": patient_id, "count": len(redacted), "memories": redacted}


@router.post("/memory/{patient_id}/reindex")
async def reindex_patient_memory(patient_id: int, db: Session = Depends(get_db)) -> dict:
    return await memory_orchestrator.reindex_patient_from_structured_data(db=db, patient_id=patient_id)

