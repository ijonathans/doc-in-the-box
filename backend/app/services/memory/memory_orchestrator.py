from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.interaction_log import InteractionLog
from app.models.patient import Patient
from app.services.memory.memory_repository import MemoryRepository


class MemoryOrchestrator:
    def __init__(self) -> None:
        self.repository = MemoryRepository()

    async def persist_profile_fact(self, patient: Patient) -> dict:
        text = (
            f"Patient profile: {patient.first_name} {patient.last_name}. "
            f"Insurance: {patient.insurance_provider}. "
            f"Chronic conditions: {patient.chronic_conditions or 'none'}."
        )
        return await self.repository.save_memory(
            memory_type="profile_fact",
            patient_id=patient.id,
            text=text,
            metadata={"source": "patient_register", "insurance_provider": patient.insurance_provider},
        )

    async def persist_symptom_visit(self, patient: Patient, symptoms_text: str, symptom_summary: str) -> dict:
        text = (
            f"Symptom visit from patient {patient.id}. "
            f"Raw symptoms: {symptoms_text.strip()}. "
            f"Summary: {symptom_summary.strip()}."
        )
        return await self.repository.save_memory(
            memory_type="symptom_visit",
            patient_id=patient.id,
            text=text,
            metadata={"source": "patient_intake", "insurance_provider": patient.insurance_provider},
        )

    async def persist_appointment_outcome(
        self,
        patient: Patient,
        appointment: Appointment,
        verification: dict,
    ) -> dict:
        text = (
            f"Appointment outcome for patient {patient.id}: status {appointment.status}. "
            f"Doctor {appointment.doctor_name}, specialty {appointment.specialty}, "
            f"time {appointment.appointment_time}. "
            f"Insurance verified {appointment.insurance_verified}. "
            f"Receptionist notes: {verification.get('receptionist_notes', '')}."
        )
        return await self.repository.save_memory(
            memory_type="appointment_outcome",
            patient_id=patient.id,
            text=text,
            metadata={
                "source": "appointment_booking",
                "status": appointment.status,
                "specialty": appointment.specialty,
                "insurance_provider": patient.insurance_provider,
            },
        )

    async def get_triage_context(
        self,
        patient: Patient,
        symptoms_text: str,
        health_history: dict,
    ) -> str:
        query_text = (
            f"Patient intake context. Symptoms: {symptoms_text}. "
            f"Conditions: {health_history.get('conditions', [])}. "
            f"Insurance: {patient.insurance_provider}."
        )
        memories = await self.repository.search_memories(patient_id=patient.id, query_text=query_text)
        if not memories:
            return "No prior long-term memory found."

        memory_lines = []
        for item in memories:
            memory_lines.append(f"- {item.get('memory_type')}: {item.get('text')}")
        return "\n".join(memory_lines)

    async def list_patient_memories(self, patient_id: int, limit: int = 20) -> list[dict]:
        return await self.repository.list_patient_memories(patient_id=patient_id, limit=limit)

    async def reindex_patient_from_structured_data(self, db: Session, patient_id: int) -> dict:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient is None:
            raise ValueError("Patient not found")

        saved = 0
        await self.persist_profile_fact(patient)
        saved += 1

        appointments = db.query(Appointment).filter(Appointment.patient_id == patient.id).all()
        for appointment in appointments:
            await self.repository.save_memory(
                memory_type="appointment_outcome",
                patient_id=patient.id,
                text=(
                    f"Historic appointment {appointment.id}: {appointment.status}, doctor {appointment.doctor_name}, "
                    f"specialty {appointment.specialty}, insurance verified {appointment.insurance_verified}."
                ),
                metadata={"source": "reindex_appointment", "status": appointment.status},
            )
            saved += 1

        interactions = db.query(InteractionLog).filter(InteractionLog.patient_id == patient.id).all()
        for interaction in interactions:
            await self.repository.save_memory(
                memory_type="symptom_visit",
                patient_id=patient.id,
                text=f"Historic interaction ({interaction.interaction_type}): {interaction.content}",
                metadata={"source": "reindex_interaction", "status": interaction.status},
            )
            saved += 1

        return {"patient_id": patient_id, "indexed_memories": saved}

