import httpx

from app.core.config import settings


class EpicFhirClient:
    def __init__(self) -> None:
        self.base_url = settings.epic_fhir_base_url.rstrip("/")
        self.client_id = settings.epic_client_id
        self.client_secret = settings.epic_client_secret

    async def get_patient_history(self, epic_patient_id: str | None) -> dict:
        if not epic_patient_id:
            return {"allergies": [], "conditions": [], "notes": "No Epic patient id linked."}

        if not self.client_id or not self.client_secret:
            return {
                "allergies": ["Penicillin"],
                "conditions": ["Hypertension"],
                "notes": "Sandbox history payload.",
            }

        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=20) as client:
            conditions_response = await client.get(
                f"{self.base_url}/Condition",
                headers=headers,
                params={"patient": epic_patient_id},
            )
            conditions_response.raise_for_status()
            conditions_payload = conditions_response.json()

        conditions = [
            entry.get("resource", {}).get("code", {}).get("text", "Unknown condition")
            for entry in conditions_payload.get("entry", [])
        ]

        return {"allergies": [], "conditions": conditions, "notes": "Fetched from Epic FHIR."}

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]

