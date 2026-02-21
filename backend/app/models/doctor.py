from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DoctorCandidate(Base):
    __tablename__ = "doctor_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_doctor_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    accepted_insurance: Mapped[str] = mapped_column(String(128), nullable=False)
    next_available_slot: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

