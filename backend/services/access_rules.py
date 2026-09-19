from datetime import datetime

from .guests import get_guest
from .reservations import get_reservation
from .properties import get_access_system


def verify_guest_access(
    guest_id: str,
    booking_id: str,
):
    guest = get_guest(guest_id)

    if guest is None:
        return {
            "allowed": False,
            "reason": "guest_not_found",
        }

    booking = get_reservation(booking_id)

    if booking is None:
        return {
            "allowed": False,
            "reason": "booking_not_found",
        }

    if booking["guest_id"] != guest_id:
        return {
            "allowed": False,
            "reason": "booking_does_not_belong_to_guest",
        }

    if booking["book_status"] != "confirmed":
        return {
            "allowed": False,
            "reason": "booking_not_confirmed",
        }

    property_id = booking["property_id"]

    access_system = get_access_system(property_id)

    if access_system is None:
        return {
            "allowed": False,
            "reason": "access_system_not_found",
        }

    now = datetime.now()

    check_in = datetime.fromisoformat(booking["check_in"])
    check_out = datetime.fromisoformat(booking["check_out"])

    if not (check_in <= now <= check_out):
        return {
            "allowed": False,
            "reason": "outside_valid_stay_window",
        }

    return {
        "allowed": True,
        "reason": "access_verified",
        "guest_id": guest_id,
        "booking_id": booking_id,
        "property_id": property_id,
        "access_system": access_system,
    }