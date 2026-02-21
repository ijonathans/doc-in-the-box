from app.tasks.celery_app import celery_app


@celery_app.task(name="agent.proactive_outreach")
def proactive_outreach_task(patient_id: int, message: str) -> dict:
    # Placeholder task for proactive outreach scheduling.
    return {"patient_id": patient_id, "message": message, "status": "queued"}

