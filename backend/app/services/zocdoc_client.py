import httpx

from app.core.config import settings

# Default for provider_locations API when no credentials (sandbox). One of specialty_id or visit_reason_id required.
DEFAULT_VISIT_REASON_ID = "pc_FRO-18leckytNKtruw5dLR"
DEFAULT_SPECIALTY_ID = "sp_153"
TOP_N_PROVIDERS = 3


class ZocDocClient:
    def __init__(self) -> None:
        self.base_url = settings.zocdoc_base_url.rstrip("/")
        self.client_id = settings.zocdoc_client_id
        self.client_secret = settings.zocdoc_client_secret

    async def get_provider_locations(
        self,
        zip_code: str,
        *,
        specialty_id: str | None = None,
        visit_reason_id: str | None = None,
        page: int = 0,
        page_size: int = TOP_N_PROVIDERS,
        max_distance_to_patient_mi: int = 50,
        insurance_plan_id: str | None = None,
    ) -> list[dict]:
        """
        GET /v1/provider_locations. Returns top 3 (or page_size) with doctor_name, phone_number, address, provider_location_id.
        One of specialty_id or visit_reason_id is required.
        """
        if not specialty_id and not visit_reason_id:
            visit_reason_id = visit_reason_id or DEFAULT_VISIT_REASON_ID
        if not self.client_id or not self.client_secret:
            return self._sandbox_provider_locations(zip_code, page_size)

        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        params: dict[str, str | int] = {
            "zip_code": zip_code,
            "page": page,
            "page_size": page_size,
            "max_distance_to_patient_mi": max_distance_to_patient_mi,
        }
        if specialty_id:
            params["specialty_id"] = specialty_id
        if visit_reason_id:
            params["visit_reason_id"] = visit_reason_id
        if insurance_plan_id:
            params["insurance_plan_id"] = insurance_plan_id

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.base_url}/v1/provider_locations",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

        data = payload.get("data") or payload
        locations = data.get("provider_locations", [])[:page_size]
        return [self._parse_provider_location(item) for item in locations]

    def _parse_provider_location(self, item: dict) -> dict:
        provider = item.get("provider") or {}
        location = item.get("location") or {}
        practice = item.get("practice") or {}
        full_name = provider.get("full_name") or (
            " ".join(filter(None, [provider.get("first_name"), provider.get("last_name")]))
        ) or "Unknown"
        address_parts = [
            location.get("address1"),
            location.get("city"),
            location.get("state"),
            location.get("zip_code"),
        ]
        address = ", ".join(str(p) for p in address_parts if p) or location.get("address") or "Unknown"
        phone = (
            location.get("phone_number")
            or practice.get("phone_number")
            or location.get("phone")
            or practice.get("phone")
            or ""
        )
        return {
            "provider_location_id": item.get("provider_location_id") or "",
            "doctor_name": full_name,
            "phone_number": phone,
            "address": address,
            "first_availability_date_in_provider_local_time": item.get(
                "first_availability_date_in_provider_local_time", ""
            ),
        }

    def _sandbox_provider_locations(self, zip_code: str, page_size: int) -> list[dict]:
        return [
            {
                "provider_location_id": "sandbox_1",
                "doctor_name": "Dr. Sarah Lin",
                "phone_number": "(404) 555-0101",
                "address": f"123 Main St, Atlanta, GA {zip_code}",
                "first_availability_date_in_provider_local_time": "2026-02-23",
            },
            {
                "provider_location_id": "sandbox_2",
                "doctor_name": "Dr. James Carter",
                "phone_number": "(404) 555-0102",
                "address": f"456 Oak Ave, Atlanta, GA {zip_code}",
                "first_availability_date_in_provider_local_time": "2026-02-24",
            },
            {
                "provider_location_id": "sandbox_3",
                "doctor_name": "Dr. Maria Santos",
                "phone_number": "(404) 555-0103",
                "address": f"789 Pine Rd, Atlanta, GA {zip_code}",
                "first_availability_date_in_provider_local_time": "2026-02-25",
            },
        ][:page_size]

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

