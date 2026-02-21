from fastapi import FastAPI

from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.patient import router as patient_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import Appointment, DoctorCandidate, InteractionLog, Patient


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hacklytics GenAI Healthcare Agent",
        version="0.1.0",
        description="Proactive AI agent for symptom triage and appointment coordination.",
    )

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(patient_router, prefix="/patient", tags=["patient"])
    app.include_router(admin_router, prefix="/admin", tags=["admin"])

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()

