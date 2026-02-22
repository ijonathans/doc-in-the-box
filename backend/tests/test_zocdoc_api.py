"""Zocdoc API integration tests: clinic details and availability."""

import pytest

from app.services.zocdoc_client import (
    DEFAULT_VISIT_REASON_ID,
    ZocDocClient,
)

REQUIRED_CLINIC_KEYS = [
    "doctor_name",
    "phone_number",
    "address",
    "provider_location_id",
    "first_availability_date_in_provider_local_time",
]

REQUIRED_SLOT_KEYS = ["provider_location_id", "start_time"]


def _print_clinic_details_and_availability(locations: list[dict]) -> None:
    """Output clinic details and first-availability for test runs (e.g. pytest -s)."""
    print("\n--- Zocdoc: clinic details and availability ---")
    for i, loc in enumerate(locations, 1):
        name = loc.get("doctor_name", "N/A")
        address = loc.get("address", "N/A")
        phone = loc.get("phone_number", "N/A")
        first_avail = loc.get("first_availability_date_in_provider_local_time", "N/A")
        print(f"  {i}. {name} — {address} — Phone: {phone} — First availability: {first_avail}")
    print("---\n")


def _print_timeslots(slots: list[dict]) -> None:
    """Output availability timeslots for test runs (e.g. pytest -s)."""
    print("\n--- Zocdoc: availability timeslots ---")
    for i, slot in enumerate(slots, 1):
        plid = slot.get("provider_location_id", "N/A")
        start = slot.get("start_time", "N/A")
        print(f"  {i}. provider_location_id={plid} — start_time={start}")
    print("---\n")


@pytest.mark.asyncio
async def test_get_clinics_and_availability():
    """
    Call Zocdoc API (or sandbox) to get provider locations; assert clinic details and
    first-availability date shape; output them so the test run shows clinic details and availability.
    Then fetch availability timeslots for those locations and assert/print them.
    """
    client = ZocDocClient()
    locations = await client.get_provider_locations(
        zip_code="30332",
        visit_reason_id=DEFAULT_VISIT_REASON_ID,
        page_size=3,
    )

    assert isinstance(locations, list)
    assert len(locations) <= 3

    for item in locations:
        assert isinstance(item, dict)
        for key in REQUIRED_CLINIC_KEYS:
            assert key in item, f"Missing key: {key}"

    _print_clinic_details_and_availability(locations)

    # Get availability timeslots for the returned provider_location_ids
    provider_location_ids = [
        loc["provider_location_id"] for loc in locations if loc.get("provider_location_id")
    ]
    if not provider_location_ids:
        return

    slots = await client.get_provider_location_availability(
        provider_location_ids=provider_location_ids,
        visit_reason_id=DEFAULT_VISIT_REASON_ID,
        patient_type="new",
    )

    assert isinstance(slots, list)
    for slot in slots:
        assert isinstance(slot, dict)
        for key in REQUIRED_SLOT_KEYS:
            assert key in slot, f"Missing slot key: {key}"

    _print_timeslots(slots)


# Expected sandbox phone numbers from ZocDocClient._sandbox_provider_locations (zocdoc_client.py)
SANDBOX_PHONE_NUMBERS = ["(912) 224-2661", "(404) 692-3162", "(912) 224-2661"]


@pytest.mark.asyncio
async def test_zocdoc_client_returns_sandbox_numbers():
    """
    Call the Zocdoc client (sandbox) and assert the returned provider locations
    contain the expected phone numbers from _sandbox_provider_locations.
    """
    client = ZocDocClient()
    locations = await client.get_provider_locations(
        zip_code="30332",
        visit_reason_id=DEFAULT_VISIT_REASON_ID,
        page_size=3,
    )

    assert len(locations) >= 1
    phones = [loc.get("phone_number", "") for loc in locations]
    for expected in SANDBOX_PHONE_NUMBERS:
        assert expected in phones, f"Expected sandbox number {expected!r} in {phones}"
    assert phones == SANDBOX_PHONE_NUMBERS[: len(locations)]
