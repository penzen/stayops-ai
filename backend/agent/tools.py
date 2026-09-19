import json

from agents.decorators import tool

from backend.services.guests import get_guest
from backend.services.reservations import get_reservation
from backend.services.properties import (
    get_property,
    get_access_system,
)
from backend.services.incidents import get_open_incidents
from backend.services.access_rules import verify_guest_access
from backend.services.messages import send_message
from backend.services.tasks import create_task_if_missing
from backend.services.escalations import create_escalation_if_missing


def as_json(data) -> str:
    return json.dumps(data, default=str)


# ---------------------------------------------------------
# READ TOOLS
# ---------------------------------------------------------


@tool
def lookup_guest(guest_id: str) -> str:
    """
    Retrieve a guest from the operational database.

    Args:
        guest_id: Unique StayOps guest ID.
    """
    guest = get_guest(guest_id)

    if guest is None:
        return as_json({
            "found": False,
            "reason": "guest_not_found",
        })

    return as_json({
        "found": True,
        "guest": guest,
    })


@tool
def lookup_reservation(booking_id: str) -> str:
    """
    Retrieve an exact reservation from the operational database.

    Args:
        booking_id: Unique reservation ID.
    """
    reservation = get_reservation(booking_id)

    if reservation is None:
        return as_json({
            "found": False,
            "reason": "reservation_not_found",
        })

    return as_json({
        "found": True,
        "reservation": reservation,
    })


@tool
def lookup_property(property_id: str) -> str:
    """
    Retrieve information about a rental property.

    Args:
        property_id: Unique StayOps property ID.
    """
    property_data = get_property(property_id)

    if property_data is None:
        return as_json({
            "found": False,
            "reason": "property_not_found",
        })

    return as_json({
        "found": True,
        "property": property_data,
    })


@tool
def lookup_access_system(property_id: str) -> str:
    """
    Retrieve the access system configured for a property.

    Args:
        property_id: Unique StayOps property ID.
    """
    access = get_access_system(property_id)

    if access is None:
        return as_json({
            "found": False,
            "reason": "access_system_not_found",
        })

    return as_json({
        "found": True,
        "access_system": access,
    })


@tool
def lookup_open_incidents(property_id: str) -> str:
    """
    Retrieve currently open operational incidents for a property.

    Args:
        property_id: Unique StayOps property ID.
    """
    incidents = get_open_incidents(property_id)

    return as_json({
        "property_id": property_id,
        "incidents": incidents,
    })


# ---------------------------------------------------------
# SAFETY / AUTHORIZATION TOOL
# ---------------------------------------------------------


@tool
def check_guest_access_permission(
    guest_id: str,
    booking_id: str,
) -> str:
    """
    Deterministically verify whether a guest is currently
    authorized for property access.

    This tool must be used before providing sensitive access
    assistance or taking access-related actions.

    Args:
        guest_id: Unique StayOps guest ID.
        booking_id: Unique reservation ID.
    """
    result = verify_guest_access(
        guest_id=guest_id,
        booking_id=booking_id,
    )

    return as_json(result)


# ---------------------------------------------------------
# ACTION TOOLS
# ---------------------------------------------------------


@tool
def message_guest(
    booking_id: str,
    guest_id: str,
    message_text: str,
) -> str:
    """
    Send and persist a message to a guest.

    Args:
        booking_id: Reservation associated with the conversation.
        guest_id: Guest receiving the message.
        message_text: Message that should be sent to the guest.
    """
    message = send_message(
        booking_id=booking_id,
        guest_id=guest_id,
        sender_type="agent",
        message_text=message_text,
    )

    return as_json({
        "success": True,
        "message": message,
    })


@tool
def create_operations_task(
    property_id: str,
    booking_id: str,
    category: str,
    title: str,
) -> str:
    """
    Ensure an operational task exists when human or physical work
    is required.

    If an equivalent open task already exists, that existing task
    will be returned rather than creating a duplicate.

    Args:
        property_id: Property where work is required.
        booking_id: Reservation associated with the issue.
        category: Operational category such as maintenance or access.
        title: Concise description of the required work.
    """

    result = create_task_if_missing(
        property_id=property_id,
        booking_id=booking_id,
        category=category,
        title=title,
    )

    return as_json(result)

def escalate_to_human(
    booking_id: str,
    property_id: str,
    category: str,
    reason: str,
    priority: str = "medium",
    incident_id: str | None = None,
) -> str:
    """
    Ensure an appropriate human escalation exists for an unresolved,
    unsafe, restricted, or ambiguous situation.

    If an open escalation already exists for the same booking,
    property, and category, that existing escalation will be returned
    rather than creating a duplicate.

    Args:
        booking_id: Reservation associated with the issue.
        property_id: Property associated with the issue.
        category: Operational category such as access, plumbing,
                  heating, electrical, maintenance, safety,
                  cleaning, wifi, refund, or other.
        reason: Why human intervention is required.
        priority: low, medium, high, or critical.
        incident_id: Existing incident ID when one is available.
    """

    result = create_escalation_if_missing(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
        incident_id=incident_id,
        reason=reason,
        priority=priority,
    )

    return as_json(result)
