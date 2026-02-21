from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    insurance_provider: Mapped[str] = mapped_column(String(128), nullable=False)
    insurance_member_id: Mapped[str] = mapped_column(String(128), nullable=False)
    epic_patient_id: Mapped[str] = mapped_column(String(128), nullable=True)
    chronic_conditions: Mapped[str] = mapped_column(Text, nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

