from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    doctor_external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    doctor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(128), nullable=False)
    appointment_time: Mapped[str] = mapped_column(String(64), nullable=False)
    clinic_location: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_verification")
    symptoms_summary: Mapped[str] = mapped_column(Text, nullable=False)
    insurance_verified: Mapped[str] = mapped_column(String(8), nullable=False, default="false")
    confirmation_sms_sent: Mapped[str] = mapped_column(String(8), nullable=False, default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

