import httpx

from app.core.config import settings


class ZocDocClient:
    def __init__(self) -> None:
        self.base_url = settings.zocdoc_base_url.rstrip("/")
        self.client_id = settings.zocdoc_client_id
        self.client_secret = settings.zocdoc_client_secret

    async def search_doctors(
        self,
        zip_code: str,
        specialty: str,
        insurance_provider: str,
    ) -> list[dict]:
        # Sandbox fallback data for initial local development.
        if not self.client_id or not self.client_secret:
            return [
                {
                    "doctor_external_id": "doc_1001",
                    "doctor_name": "Dr. Sarah Lin",
                    "specialty": specialty,
                    "location": f"{zip_code} - Downtown Clinic",
                    "next_available_slot": "2026-02-23T10:30:00",
                    "accepted_insurance": insurance_provider,
                },
                {
                    "doctor_external_id": "doc_1002",
                    "doctor_name": "Dr. James Carter",
                    "specialty": specialty,
                    "location": f"{zip_code} - East Medical Group",
                    "next_available_slot": "2026-02-23T13:00:00",
                    "accepted_insurance": insurance_provider,
                },
            ]

        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {"specialty": specialty, "zip_code": zip_code, "insurance_provider": insurance_provider}

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/v1/provider_locations", headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()

        doctors: list[dict] = []
        for item in payload.get("provider_locations", []):
            doctors.append(
                {
                    "doctor_external_id": str(item.get("provider_location_id", "")),
                    "doctor_name": item.get("provider_name", "Unknown"),
                    "specialty": specialty,
                    "location": item.get("address", "Unknown"),
                    "next_available_slot": item.get("next_available_slot", ""),
                    "accepted_insurance": insurance_provider,
                }
            )
        return doctors

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]

