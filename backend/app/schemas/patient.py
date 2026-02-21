from pydantic import BaseModel


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    insurance_provider: str
    insurance_member_id: str
    epic_patient_id: str | None = None
    chronic_conditions: str | None = None


class PatientOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone_number: str
    insurance_provider: str
    insurance_member_id: str
    epic_patient_id: str | None = None
    chronic_conditions: str | None = None

    class Config:
        from_attributes = True

