from mcp.server import MCPServer
from backend.services.guests import get_guest
from backend.services.reservations import get_reservation
from backend.domain.enums import Priority
from backend.services.properties import (
    get_property,
    get_access_system,
)
from backend.services.incidents import get_open_incidents
from backend.services.access_rules import verify_guest_access

from backend.services.tasks import create_task_if_missing
from backend.services.escalations import create_escalation_if_missing

from backend.services.cases import (
    get_case,
    get_case_context,
    get_open_cases_for_booking,
    ensure_case,
    transition_case_status,
    resolve_case_if_ready,
)

mcp = MCPServer("StayOps Operations")


# ---------------------------------------------------------
# GUESTS
# ---------------------------------------------------------


@mcp.tool()
def lookup_guest(guest_id: str) -> dict:
    """
    Retrieve a guest from the StayOps operational database.
    """

    guest = get_guest(guest_id)

    if guest is None:
        return {
            "found": False,
            "reason": "guest_not_found",
        }

    return {
        "found": True,
        "guest": guest,
    }


# ---------------------------------------------------------
# RESERVATIONS
# ---------------------------------------------------------


@mcp.tool()
def lookup_reservation(booking_id: str) -> dict:
    """
    Retrieve a reservation using its unique booking ID.
    """

    reservation = get_reservation(booking_id)

    if reservation is None:
        return {
            "found": False,
            "reason": "reservation_not_found",
        }

    return {
        "found": True,
        "reservation": reservation,
    }


# ---------------------------------------------------------
# PROPERTIES
# ---------------------------------------------------------


@mcp.tool()
def lookup_property(property_id: str) -> dict:
    """
    Retrieve operational information about a rental property.
    """

    property_data = get_property(property_id)

    if property_data is None:
        return {
            "found": False,
            "reason": "property_not_found",
        }

    return {
        "found": True,
        "property": property_data,
    }


@mcp.tool()
def lookup_access_system(property_id: str) -> dict:
    """
    Retrieve the access system configured for a property.
    """

    access = get_access_system(property_id)

    if access is None:
        return {
            "found": False,
            "reason": "access_system_not_found",
        }

    return {
        "found": True,
        "access_system": access,
    }


# ---------------------------------------------------------
# INCIDENTS
# ---------------------------------------------------------


@mcp.tool()
def lookup_open_incidents(property_id: str) -> dict:
    """
    Retrieve open operational incidents for a property.
    """

    incidents = get_open_incidents(property_id)

    return {
        "property_id": property_id,
        "incidents": incidents,
    }


# ---------------------------------------------------------
# ACCESS AUTHORIZATION
# ---------------------------------------------------------


@mcp.tool()
def check_guest_access_permission(
    guest_id: str,
    booking_id: str,
) -> dict:
    """
    Deterministically verify whether a guest is currently
    authorized for property access.

    This must be checked before sensitive access assistance.
    """

    return verify_guest_access(
        guest_id=guest_id,
        booking_id=booking_id,
    )


# ---------------------------------------------------------
# CASES
# ---------------------------------------------------------


@mcp.tool()
def lookup_case(case_id: str) -> dict:
    """
    Retrieve one operational Case by its unique Case ID.
    """

    case = get_case(case_id)

    if case is None:
        return {
            "found": False,
            "reason": "case_not_found",
        }

    return {
        "found": True,
        "case": case,
    }

@mcp.tool()
def lookup_case_context(case_id: str) -> dict:
    """
    Retrieve the current operational context for a Case,
    including Case-owned tasks, Case-owned escalations,
    and recent booking conversation.
    """

    context = get_case_context(case_id)

    if context is None:
        return {
            "found": False,
            "reason": "case_not_found",
        }

    return {
        "found": True,
        "context": context,
    }

@mcp.tool()
def lookup_open_cases_for_booking(
    booking_id: str,
) -> dict:
    """
    Retrieve all open operational Cases for a booking.

    Use this when determining whether a guest message is a
    follow-up to an already active operational issue.
    """

    cases = get_open_cases_for_booking(booking_id)

    return {
        "booking_id": booking_id,
        "cases": cases,
    }

@mcp.tool()
def ensure_operational_case(
    booking_id: str,
    property_id: str,
    category: str,
    summary: str | None = None,
) -> dict:
    """
    Ensure that an open operational Case exists for the same
    booking, property, and issue category.

    Reuse an existing open Case instead of creating a duplicate.
    """

    return ensure_case(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
        summary=summary,
    )

@mcp.tool()
def update_case_workflow_status(
    case_id: str,
    new_status: str,
) -> dict:
    """
    Update the workflow state of an active operational Case.

    Agent-settable states:
    - in_progress
    - waiting_guest
    - waiting_human

    Case resolution is handled separately and cannot be
    performed through this tool.
    """

    allowed_statuses = {
        "in_progress",
        "waiting_guest",
        "waiting_human",
    }

    normalized_status = new_status.strip().lower()

    if normalized_status not in allowed_statuses:
        return {
            "updated": False,
            "reason": "status_not_agent_settable",
            "allowed_statuses": sorted(allowed_statuses),
        }

    return transition_case_status(
        case_id=case_id,
        new_status=normalized_status,
    )

@mcp.tool()
def attempt_case_resolution(
    case_id: str,
) -> dict:
    """
    Attempt to resolve an operational Case.

    Resolution is determined by deterministic operational
    evidence, not by the agent.

    The Case resolves only when:
    - resolution evidence exists, and
    - no linked task remains open, and
    - no linked escalation remains open.

    If those conditions are not satisfied, resolution is blocked
    and the Case remains active.
    """

    return resolve_case_if_ready(
        case_id=case_id,
    )

# ---------------------------------------------------------
# OPERATIONAL TASKS
# ---------------------------------------------------------


@mcp.tool()
def ensure_operations_task(
    property_id: str,
    booking_id: str,
    category: str,
    title: str,
    case_id: str | None = None,
) -> dict:
    """
    Ensure that an open operational task exists.

    If an equivalent task is already open, return it instead
    of creating a duplicate.
    """

    return create_task_if_missing(
        property_id=property_id,
        booking_id=booking_id,
        category=category,
        title=title,
        case_id=case_id,
    )


# ---------------------------------------------------------
# HUMAN ESCALATION
# ---------------------------------------------------------


@mcp.tool()
def ensure_human_escalation(
    booking_id: str,
    property_id: str,
    category: str,
    reason: str,
    priority: str = Priority.MEDIUM,
    incident_id: str | None = None,
    case_id: str | None = None,
):
    """
    Create a human escalation if an open escalation for the same
    booking, property, and category does not already exist.
    """

    return create_escalation_if_missing(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
        reason=reason,
        priority=priority,
        incident_id=incident_id,
        case_id=case_id,
    )


if __name__ == "__main__":
    mcp.run()