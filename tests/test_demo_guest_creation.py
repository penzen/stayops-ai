from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.demo import (
    get_demo_stays,
    reset_demo_state,
)
from backend.services.demo_guests import (
    create_demo_guest_stay,
    get_demo_properties,
)
from backend.services.guests import get_guest
from backend.services.messages import (
    get_booking_messages,
    send_message,
)
from backend.services.reservations import (
    get_reservation,
)


client = TestClient(app)


def test_demo_properties_are_available(
    test_db,
):
    properties = get_demo_properties()

    assert len(properties) > 0
    assert properties[0]["property_id"]
    assert properties[0]["title"]


def test_create_demo_guest_stay_persists_guest_and_booking(
    test_db,
):
    created = create_demo_guest_stay(
        first_name="Maya",
        last_name="Patel",
        email="maya@example.com",
        guest_lang="en",
        property_id="prop_15",
    )

    assert created["guest_id"].startswith(
        "gst_demo_custom_"
    )
    assert created["booking_id"].startswith(
        "book_demo_custom_"
    )
    assert created["book_status"] == "confirmed"
    assert created["property_id"] == "prop_15"

    guest = get_guest(
        created["guest_id"]
    )
    reservation = get_reservation(
        created["booking_id"]
    )

    assert guest is not None
    assert guest["first_name"] == "Maya"
    assert guest["last_name"] == "Patel"
    assert guest["guest_lang"] == "en"

    assert reservation is not None
    assert (
        reservation["guest_id"]
        == created["guest_id"]
    )
    assert reservation["source"] == "StayOps Demo"


def test_custom_demo_stay_appears_in_demo_stays_and_resets(
    test_db,
):
    created = create_demo_guest_stay(
        first_name="Lena",
        last_name="Fischer",
        guest_lang="de",
        property_id="prop_15",
    )

    booking_id = created["booking_id"]
    guest_id = created["guest_id"]

    stays = get_demo_stays()

    assert any(
        stay["booking_id"] == booking_id
        for stay in stays
    )

    send_message(
        booking_id=booking_id,
        guest_id=guest_id,
        sender_type="guest",
        message_text="The heating is broken.",
    )

    assert len(
        get_booking_messages(booking_id)
    ) == 1

    result = reset_demo_state(
        booking_id
    )

    assert result["status"] == "reset"
    assert (
        result["deleted"]["messages"]
        == 1
    )
    assert (
        get_booking_messages(booking_id)
        == []
    )


def test_create_demo_stay_endpoint(
    test_db,
):
    response = client.post(
        "/demo/stays",
        json={
            "first_name": "Noah",
            "last_name": "Martin",
            "email": None,
            "guest_lang": "fr",
            "property_id": "prop_15",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["first_name"] == "Noah"
    assert data["last_name"] == "Martin"
    assert data["guest_lang"] == "fr"
    assert data["booking_id"].startswith(
        "book_demo_custom_"
    )


def test_create_demo_stay_rejects_unknown_property(
    test_db,
):
    response = client.post(
        "/demo/stays",
        json={
            "first_name": "Test",
            "last_name": "Guest",
            "guest_lang": "en",
            "property_id": "prop_missing",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Selected property does not exist."
    )
