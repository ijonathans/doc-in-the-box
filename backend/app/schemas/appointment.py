from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_external_id: str
    doctor_name: str
    specialty: str
    appointment_time: str
    clinic_location: str
    symptoms_summary: str


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_external_id: str
    doctor_name: str
    specialty: str
    appointment_time: str
    clinic_location: str
    status: str
    symptoms_summary: str
    insurance_verified: str
    confirmation_sms_sent: str

    class Config:
        from_attributes = True

