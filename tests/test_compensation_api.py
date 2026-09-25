from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.cases import ensure_case
from backend.services.compensation import (
    ensure_compensation_request,
)


client = TestClient(app)

BOOKING_ID = "book_demo_current_001"
PROPERTY_ID = "prop_15"


def create_compensation_request():
    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    result = ensure_compensation_request(
        case_id=refund_case["case"]["case_id"],
        reason="Heating disruption.",
        requested_outcome="Refund requested.",
    )

    return result["compensation_request"]


def test_get_compensation_evidence_endpoint(
    test_db,
):
    request = create_compensation_request()

    request_id = request[
        "compensation_request_id"
    ]

    response = client.get(
        f"/compensation-requests/{request_id}/evidence"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["compensation_request"][
            "compensation_request_id"
        ]
        == request_id
    )

    assert data["decision"] is None


def test_human_can_record_compensation_decision_via_api(
    test_db,
):
    request = create_compensation_request()

    request_id = request[
        "compensation_request_id"
    ]

    response = client.post(
        f"/compensation-requests/{request_id}/decision",
        json={
            "decision": "approved",
            "decided_by": "ops_manager_001",
            "amount": 125.00,
            "currency": "EUR",
            "reason": (
                "Approved after operational review."
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["created"] is True
    assert data["decision"]["decision"] == "approved"
    assert data["decision"]["amount"] == 125.00
    assert data["decision"]["currency"] == "EUR"


def test_invalid_financial_decision_returns_400(
    test_db,
):
    request = create_compensation_request()

    request_id = request[
        "compensation_request_id"
    ]

    response = client.post(
        f"/compensation-requests/{request_id}/decision",
        json={
            "decision": "approved",
            "decided_by": "ops_manager_001",
            "reason": (
                "Attempted approval without amount."
            ),
        },
    )

    assert response.status_code == 400