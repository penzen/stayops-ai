from mcp.server import MCPServer
from backend.services.guests import get_guest
from backend.services.reservations import get_reservation
from backend.domain.enums import Priority
from backend.domain.playbooks import get_playbook
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
    get_recent_cases_for_booking,
    ensure_case,
    transition_case_status,
    resolve_case_if_ready,
)

from backend.services.compensation import (
    ensure_compensation_request as ensure_compensation_request_service,
    ensure_refund_workflow as ensure_refund_workflow_service,
    get_compensation_request_by_case,
    get_compensation_evidence,
    build_compensation_assessment,
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
# OPERATIONAL PLAYBOOKS
# ---------------------------------------------------------


@mcp.tool()
def lookup_operational_playbook(
    category: str,
) -> dict:
    """
    Retrieve the approved structured operational playbook
    for an issue category.

    Playbooks define StayOps operational policy, required
    checks, safe actions, prohibited actions, operational
    actions, priority conditions, and resolution conditions.
    """

    playbook = get_playbook(category)

    if playbook is None:
        return {
            "found": False,
            "reason": "playbook_not_found",
            "category": category,
        }

    return {
        "found": True,
        "playbook": playbook,
    }

# ---------------------------------------------------------
# COMPENSATION
# ---------------------------------------------------------

@mcp.tool()
def ensure_refund_workflow(
    booking_id: str,
    property_id: str,
    reason: str,
    requested_outcome: str | None = None,
    related_case_id: str | None = None,
    explicit_new_request: bool = False,
) -> dict:
    """
    Create, reuse, or recover the complete refund workflow.

    This tool deterministically handles:
    - active refund Cases,
    - new refund Cases,
    - compensation requests,
    - human financial escalations,
    - waiting_human workflow state,
    - historical resolved refund follow-ups.

    By default, a previous resolved refund is treated as historical
    rather than creating a duplicate financial workflow.

    Set explicit_new_request=True only when the guest is clearly
    making a distinct new financial request.
    """

    return ensure_refund_workflow_service(
        booking_id=booking_id,
        property_id=property_id,
        reason=reason,
        requested_outcome=requested_outcome,
        related_case_id=related_case_id,
        explicit_new_request=explicit_new_request,
    )

@mcp.tool()
def ensure_compensation_review(
    case_id: str,
    reason: str,
    requested_outcome: str | None = None,
    related_case_id: str | None = None,
) -> dict:
    """
    Create or reuse the compensation request owned by a
    refund Case.

    This records the guest's request for human financial
    review. It does not approve, deny, or determine an amount.
    """

    return ensure_compensation_request_service(
        case_id=case_id,
        reason=reason,
        requested_outcome=requested_outcome,
        related_case_id=related_case_id,
    )


@mcp.tool()
def lookup_compensation_evidence(
    compensation_request_id: str,
) -> dict:
    """
    Retrieve the deterministic operational evidence connected
    to a compensation request.

    This is evidence for review only and does not make a
    financial decision.
    """

    try:
        evidence = get_compensation_evidence(
            compensation_request_id
        )

        return {
            "found": True,
            "evidence": evidence,
        }

    except ValueError:
        return {
            "found": False,
            "reason": "compensation_request_not_found",
        }


@mcp.tool()
def assess_compensation_request(
    compensation_request_id: str,
) -> dict:
    """
    Build a deterministic compensation assessment from the
    available operational evidence.

    The assessment may describe severity and review factors,
    but cannot approve, deny, or assign money.
    """

    return build_compensation_assessment(
        compensation_request_id
    )


# ---------------------------------------------------------
# OPERATIONAL TASKS
# ---------------------------------------------------------

@mcp.tool()
def lookup_recent_cases_for_booking(
    booking_id: str,
    category: str | None = None,
    limit: int = 5,
) -> dict:
    """
    Retrieve recent Case history for a booking, including resolved
    Cases.

    Use this for follow-up questions about an issue that may already
    have completed its workflow.
    """

    cases = get_recent_cases_for_booking(
        booking_id=booking_id,
        category=category,
        limit=limit,
    )

    return {
        "booking_id": booking_id,
        "category": category,
        "cases": cases,
    }

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

@mcp.tool()
def lookup_compensation_review_for_case(
    case_id: str,
) -> dict:
    """
    Retrieve the compensation workflow associated with a refund Case.

    This allows the agent to rediscover the compensation request
    from persistent Case state on later conversation turns.

    The returned evidence may contain a recorded human financial
    decision. This tool does not create or modify that decision.
    """

    request = get_compensation_request_by_case(
        case_id
    )

    if request is None:
        return {
            "found": False,
            "reason": "compensation_request_not_found",
            "case_id": case_id,
        }

    evidence = get_compensation_evidence(
        request["compensation_request_id"]
    )

    return {
        "found": True,
        "compensation_request": request,
        "evidence": evidence,
    }

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

    Refund escalations require an existing refund Case and
    compensation request so the financial workflow cannot be
    bypassed.
    """

    normalized_category = (
        category.strip().lower()
    )

    # -----------------------------------------------------
    # FINANCIAL WORKFLOW GUARD
    # -----------------------------------------------------

    if normalized_category == "refund":

        if case_id is None:
            return {
                "created": False,
                "reason":
                    "refund_case_required",
                "required_action":
                    (
                        "Create or reuse a refund Case first "
                        "with ensure_operational_case, then "
                        "create the compensation review with "
                        "ensure_compensation_review."
                    ),
            }

        case = get_case(
            case_id
        )

        if case is None:
            return {
                "created": False,
                "reason":
                    "refund_case_not_found",
            }

        if case["category"] != "refund":
            return {
                "created": False,
                "reason":
                    "refund_case_required",
                "required_action":
                    (
                        "Refund escalations must belong "
                        "to a refund Case."
                    ),
            }

        compensation_request = (
            get_compensation_request_by_case(
                case_id
            )
        )

        if compensation_request is None:
            return {
                "created": False,
                "reason":
                    "compensation_review_required",
                "required_action":
                    (
                        "Create or reuse the compensation "
                        "review before escalating the "
                        "financial request."
                    ),
            }

    return create_escalation_if_missing(
        booking_id=booking_id,
        property_id=property_id,
        category=normalized_category,
        reason=reason,
        priority=priority,
        incident_id=incident_id,
        case_id=case_id,
    )


if __name__ == "__main__":
    mcp.run()