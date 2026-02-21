from twilio.rest import Client

from app.core.config import settings


class SmsService:
    def __init__(self) -> None:
        self.client = (
            Client(settings.twilio_account_sid, settings.twilio_auth_token)
            if settings.twilio_account_sid and settings.twilio_auth_token
            else None
        )

    def send_appointment_confirmation(self, to_phone: str, message: str) -> dict:
        if not self.client:
            return {"status": "queued_mock", "sid": "mock-sid"}

        sms = self.client.messages.create(
            body=message,
            from_=settings.twilio_phone_number,
            to=to_phone,
        )
        return {"status": sms.status, "sid": sms.sid}

