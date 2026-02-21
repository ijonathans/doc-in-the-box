from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.interaction_log import InteractionLog
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate
from app.services.elevenlabs_call_agent import ElevenLabsCallAgent
from app.services.memory.memory_orchestrator import MemoryOrchestrator
from app.services.sms_service import SmsService


class SchedulerService:
    def __init__(self) -> None:
        self.call_agent = ElevenLabsCallAgent()
        self.sms_service = SmsService()
        self.memory_orchestrator = MemoryOrchestrator()

    async def create_and_confirm_appointment(self, db: Session, payload: AppointmentCreate) -> Appointment:
        patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
        if patient is None:
            raise ValueError("Patient not found")

        appointment = Appointment(
            patient_id=payload.patient_id,
            doctor_external_id=payload.doctor_external_id,
            doctor_name=payload.doctor_name,
            specialty=payload.specialty,
            appointment_time=payload.appointment_time,
            clinic_location=payload.clinic_location,
            symptoms_summary=payload.symptoms_summary,
        )
        db.add(appointment)
        db.flush()

        verification = await self.call_agent.verify_and_book(
            {
                "office_phone": "+10000000000",
                "patient_name": f"{patient.first_name} {patient.last_name}",
                "insurance_provider": patient.insurance_provider,
                "doctor_name": payload.doctor_name,
                "appointment_time": payload.appointment_time,
            }
        )
        appointment.insurance_verified = "true" if verification["insurance_in_network"] else "false"
        appointment.status = "booked" if verification["slot_confirmed"] else "verification_failed"

        if appointment.status == "booked":
            sms = self.sms_service.send_appointment_confirmation(
                to_phone=patient.phone_number,
                message=(
                    f"Appointment confirmed with {payload.doctor_name} "
                    f"at {payload.appointment_time} ({payload.clinic_location})."
                ),
            )
            appointment.confirmation_sms_sent = "true" if sms["status"] else "false"

        db.add(
            InteractionLog(
                patient_id=patient.id,
                interaction_type="appointment_booking",
                channel="voice",
                content=str(verification),
                status=appointment.status,
            )
        )

        await self.memory_orchestrator.persist_appointment_outcome(
            patient=patient,
            appointment=appointment,
            verification=verification,
        )
        db.commit()
        db.refresh(appointment)
        return appointment

