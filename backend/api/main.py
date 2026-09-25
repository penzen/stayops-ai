from fastapi import FastAPI, HTTPException
from backend.services.access_rules import verify_guest_access
from backend.domain.enums import SenderType
from fastapi.middleware.cors import CORSMiddleware
from backend.services.demo import (
    get_demo_stays,
    reset_demo_state,
)
from backend.services.audit import get_case_timeline

from backend.api.schemas import (
    MessageCreate,
    IncidentCreate,
    TaskCreate,
    EscalationCreate,
    AgentChatRequest,
    AgentChatResponse,
    CompensationDecisionCreate,
    CaseOperatorAction,
)
from backend.services.compensation import (
    get_compensation_evidence,
    record_compensation_decision,
)

from backend.services.cases import (
    get_case,
    get_open_cases_for_booking,
    get_human_operations_queue,
    claim_case,
    return_case_to_agent,
)

from backend.agent.guest_agent import run_guest_agent

from backend.services.guests import get_guest

from backend.services.reservations import (
    get_reservation,
    get_guest_reservations,
)

from backend.services.properties import (
    get_property,
    get_access_system,
)

from backend.services.incidents import (
    get_open_incidents,
    create_incident,
    resolve_incident,
)

from backend.services.messages import (
    send_message,
    get_booking_messages,
)

from backend.services.tasks import (
    create_task,
    get_open_tasks,
    complete_task,
)

from backend.services.escalations import (
    create_escalation,
    get_open_escalations,
    resolve_escalation,
)


app = FastAPI(
    title="StayOps API",
    description="Operational backend for the StayOps autonomous guest-operations system.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://d8hbj9y50bgwb.cloudfront.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "stayops-api",
    }


# ---------------------------------------------------------
# GUESTS
# ---------------------------------------------------------

@app.get("/guests/{guest_id}")
def read_guest(guest_id: str):
    guest = get_guest(guest_id)

    if guest is None:
        raise HTTPException(
            status_code=404,
            detail="Guest not found",
        )

    return guest


@app.get("/guests/{guest_id}/reservations")
def read_guest_reservations(guest_id: str):
    return get_guest_reservations(guest_id)


# ---------------------------------------------------------
# RESERVATIONS
# ---------------------------------------------------------

@app.get("/reservations/{booking_id}")
def read_reservation(booking_id: str):
    reservation = get_reservation(booking_id)

    if reservation is None:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found",
        )

    return reservation


@app.get("/reservations/{booking_id}/messages")
def read_booking_messages(booking_id: str):
    return get_booking_messages(booking_id)


# ---------------------------------------------------------
# HUMAN OPERATIONS
# ---------------------------------------------------------

@app.get("/operations/queue")
def read_human_operations_queue():
    return get_human_operations_queue()


@app.patch("/cases/{case_id}/claim")
def claim_case_for_operator(
    case_id: str,
    payload: CaseOperatorAction,
):
    try:
        return claim_case(
            case_id=case_id,
            operator_id=payload.operator_id,
        )

    except ValueError as exc:
        detail = str(exc)

        status_code = (
            404
            if detail.startswith("Case does not exist:")
            else 409
        )

        raise HTTPException(
            status_code=status_code,
            detail=detail,
        )


@app.patch("/cases/{case_id}/return-to-agent")
def return_case_to_agent_endpoint(
    case_id: str,
    payload: CaseOperatorAction,
):
    try:
        return return_case_to_agent(
            case_id=case_id,
            operator_id=payload.operator_id,
        )

    except ValueError as exc:
        detail = str(exc)

        status_code = (
            404
            if detail.startswith("Case does not exist:")
            else 409
        )

        raise HTTPException(
            status_code=status_code,
            detail=detail,
        )
# ---------------------------------------------------------
# CASES
# ---------------------------------------------------------

@app.get("/cases/{case_id}")
def read_case(case_id: str):
    case = get_case(case_id)

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return case

@app.get("/cases/{case_id}/timeline")
def read_case_timeline(case_id: str):
    try:
        return get_case_timeline(case_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@app.get("/reservations/{booking_id}/cases")
def read_booking_cases(booking_id: str):
    return get_open_cases_for_booking(booking_id)

# ---------------------------------------------------------
# PROPERTIES
# ---------------------------------------------------------

@app.get("/properties/{property_id}")
def read_property(property_id: str):
    property_data = get_property(property_id)

    if property_data is None:
        raise HTTPException(
            status_code=404,
            detail="Property not found",
        )

    return property_data


@app.get("/properties/{property_id}/access")
def read_access_system(property_id: str):
    access = get_access_system(property_id)

    if access is None:
        raise HTTPException(
            status_code=404,
            detail="Access system not found",
        )

    return access


@app.get("/properties/{property_id}/incidents")
def read_open_incidents(property_id: str):
    return get_open_incidents(property_id)


@app.get("/properties/{property_id}/tasks")
def read_open_tasks(property_id: str):
    return get_open_tasks(property_id)


# ---------------------------------------------------------
# MESSAGES
# ---------------------------------------------------------

@app.post("/messages")
def create_message(payload: MessageCreate):
    return send_message(
        booking_id=payload.booking_id,
        guest_id=payload.guest_id,
        sender_type=payload.sender_type,
        message_text=payload.message_text,
        channel=payload.channel,
    )


# ---------------------------------------------------------
# INCIDENTS
# ---------------------------------------------------------

@app.post("/incidents")
def create_new_incident(payload: IncidentCreate):
    return create_incident(
        property_id=payload.property_id,
        booking_id=payload.booking_id,
        category=payload.category,
        description=payload.description,
        severity=payload.severity,
    )


@app.patch("/incidents/{incident_id}/resolve")
def resolve_existing_incident(incident_id: str):
    incident = resolve_incident(incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return incident


# ---------------------------------------------------------
# TASKS
# ---------------------------------------------------------

@app.post("/tasks")
def create_new_task(payload: TaskCreate):
    return create_task(
        property_id=payload.property_id,
        booking_id=payload.booking_id,
        category=payload.category,
        title=payload.title,
        assigned_by=payload.assigned_by,
        assigned_to=payload.assigned_to,
        parent_task_id=payload.parent_task_id,
    )

@app.patch("/tasks/{task_id}/complete")
def complete_existing_task(task_id: str):
    task = complete_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task


# ---------------------------------------------------------
# ESCALATIONS
# ---------------------------------------------------------

@app.post("/escalations")
def create_new_escalation(payload: EscalationCreate):
    return create_escalation(
        booking_id=payload.booking_id,
        property_id=payload.property_id,
        incident_id=payload.incident_id,
        category=payload.category,
        reason=payload.reason,
        priority=payload.priority,
        assigned_to=payload.assigned_to,
    )


@app.get("/escalations")
def read_open_escalations():
    return get_open_escalations()


@app.get("/access/verify")
def verify_access(
    guest_id: str,
    booking_id: str,
):
    return verify_guest_access(
        guest_id=guest_id,
        booking_id=booking_id,
    )

@app.patch("/escalations/{escalation_id}/resolve")
def resolve_existing_escalation(
    escalation_id: str,
):
    escalation = resolve_escalation(
        escalation_id
    )

    if escalation is None:
        raise HTTPException(
            status_code=404,
            detail="Escalation not found",
        )

    return escalation

# ---------------------------------------------------------
# COMPENSATION
# ---------------------------------------------------------


@app.get(
    "/compensation-requests/{compensation_request_id}/evidence"
)
def read_compensation_evidence(
    compensation_request_id: str,
):
    try:
        return get_compensation_evidence(
            compensation_request_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@app.post(
    "/compensation-requests/{compensation_request_id}/decision"
)
def create_compensation_decision(
    compensation_request_id: str,
    payload: CompensationDecisionCreate,
):
    try:
        return record_compensation_decision(
            compensation_request_id=(
                compensation_request_id
            ),
            decision=payload.decision,
            decided_by=payload.decided_by,
            reason=payload.reason,
            amount=payload.amount,
            currency=payload.currency,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

# ---------------------------------------------------------
# AGENT
# ---------------------------------------------------------

@app.post(
    "/agent/chat",
    response_model=AgentChatResponse,
)
async def agent_chat(payload: AgentChatRequest):
    """
    Send a guest message through the StayOps Guest Operations Agent.

    The agent can:
    - retrieve operational state
    - retrieve StayOps knowledge
    - create/reuse tasks
    - create/reuse escalations
    - send guest messages
    - apply deterministic safety rules
    """

    try:
        # -----------------------------------------------------
        # LOAD EXISTING MULTI-TURN CONTEXT
        # -----------------------------------------------------

        open_cases = get_open_cases_for_booking(
            payload.booking_id
        )

        recent_messages = get_booking_messages(
            payload.booking_id
        )[-6:]

        # -----------------------------------------------------
        # PERSIST CURRENT GUEST MESSAGE
        # -----------------------------------------------------

        send_message(
            booking_id=payload.booking_id,
            guest_id=payload.guest_id,
            sender_type=SenderType.GUEST,
            message_text=payload.message,
        )

        # -----------------------------------------------------
        # RUN AGENT
        # -----------------------------------------------------

        result = await run_guest_agent(
            guest_id=payload.guest_id,
            booking_id=payload.booking_id,
            message=payload.message,
            scenario_name="api_guest_chat",
            show_tools=False,
            open_cases=open_cases,
            recent_messages=recent_messages,
        )

        # Persist the outgoing agent response deterministically.
        send_message(
            booking_id=payload.booking_id,
            guest_id=payload.guest_id,
            sender_type=SenderType.AGENT,
            message_text=result.final_output,
        )
        
        activity_labels = {
            "lookup_guest": "Guest profile retrieved",
            "lookup_reservation": "Reservation retrieved",
            "lookup_property": "Property context retrieved",
            "lookup_access_system": "Access system retrieved",
            "lookup_open_incidents": "Open incidents checked",
            "check_guest_access_permission": "Access permission verified",
            "qdrant-find": "StayOps operational knowledge retrieved",
            "ensure_operations_task": "Operations task created or reused",
            "ensure_human_escalation": "Human escalation created or reused",
            "lookup_case": "Operational case retrieved",
            "ensure_operational_case": "Operational case created or reused",
            "lookup_case_context": "Operational case context retrieved",
            "lookup_open_cases_for_booking": "Open operational cases checked",
            "update_case_workflow_status": "Operational case status updated",
            "attempt_case_resolution": "Operational case resolution checked",
            "lookup_operational_playbook": "Operational playbook retrieved",
            "ensure_compensation_review":"Compensation request created or reused",
            "lookup_compensation_evidence":"Compensation evidence reviewed",
            "assess_compensation_request":"Compensation assessment prepared",
            "lookup_compensation_review_for_case":"Compensation review retrieved",
            "lookup_recent_cases_for_booking":"Operational case history retrieved",
        }

        activities = []

        for item in result.new_items:
            if getattr(item, "type", None) != "tool_call_item":
                continue

            tool_name = getattr(
                item,
                "tool_name",
                None,
            )

            if not isinstance(tool_name, str):
                    continue

            label = activity_labels.get(tool_name)

            if label and label not in activities:
                activities.append(label)
                

        return {
            "guest_id": payload.guest_id,
            "booking_id": payload.booking_id,
            "response": result.final_output,
            "activities": activities,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {exc}",
        ) from exc

# ---------------------------------------------------------
# DEMO
# ---------------------------------------------------------

@app.get("/demo/stays")
def read_demo_stays():
    return get_demo_stays()


@app.post("/demo/reset/{booking_id}")
def reset_demo(
    booking_id: str,
):
    try:
        return reset_demo_state(
            booking_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc