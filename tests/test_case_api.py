from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.cases import ensure_case


client = TestClient(app)

PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"


def test_get_case_endpoint(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    case_id = case_result["case"]["case_id"]

    response = client.get(
        f"/cases/{case_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["case_id"] == case_id
    assert data["booking_id"] == BOOKING_ID
    assert data["property_id"] == PROPERTY_ID
    assert data["category"] == "plumbing"


def test_get_booking_cases_endpoint(test_db):
    plumbing_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Kitchen sink leak.",
    )

    heating_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure.",
    )

    response = client.get(
        f"/reservations/{BOOKING_ID}/cases"
    )

    assert response.status_code == 200

    data = response.json()

    case_ids = {
        case["case_id"]
        for case in data
    }

    assert plumbing_case["case"]["case_id"] in case_ids
    assert heating_case["case"]["case_id"] in case_ids