import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from agents.mcp import MCPServerManager
from backend.services.access_rules import verify_guest_access
from backend.domain.enums import SenderType
from fastapi.middleware.cors import CORSMiddleware
from backend.services.demo import (
    get_demo_stays,
    reset_demo_state,
)
from backend.services.audit import get_case_timeline
from backend.services.demo_guests import (
    create_demo_guest_stay,
    get_demo_properties,
)
from backend.services.demo_sessions import (
    DemoSessionAccessDenied,
    DemoSessionExpired,
    DemoSessionUnauthorized,
    create_demo_session,
    get_demo_session_booking_ids,
    get_demo_session_stays,
    require_demo_booking_access,
    require_demo_case_access,
    require_demo_compensation_access,
    require_demo_escalation_access,
    require_demo_guest_access,
    require_demo_incident_access,
    require_demo_task_access,
    validate_demo_session,
)

from backend.api.schemas import (
    MessageCreate,
    IncidentCreate,
    TaskCreate,
    EscalationCreate,
    AgentChatRequest,
    AgentChatResponse,
    CompensationDecisionCreate,
    CaseOperatorAction,
    TaskAssignmentAction,
    DemoGuestStayCreate,
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
    get_recent_cases_for_booking,

)
from backend.services.teams import (
    get_maintenance_workers,
)

from backend.agent.guest_agent import (
    create_knowledge_mcp_server,
    create_operations_mcp_server,
    run_guest_agent,
)

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
    assign_task,
)

from backend.services.escalations import (
    create_escalation,
    get_open_escalations,
    resolve_escalation,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    servers = [
        create_operations_mcp_server(),
        create_knowledge_mcp_server(),
    ]

    async with MCPServerManager(
        servers,
        strict=True,
        connect_in_parallel=True,
        connect_timeout_seconds=180.0,
        cleanup_timeout_seconds=30.0,
    ) as manager:
        app.state.mcp_servers = manager.active_servers
        yield


app = FastAPI(
    title="StayOps API",
    description="Operational backend for the StayOps autonomous guest-operations system.",
    version="0.1.0",
    lifespan=lifespan,
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
# DEMO SESSION AUTH
# ---------------------------------------------------------

def require_demo_session(
    x_stayops_demo_token: str | None = Header(
        default=None,
        alias="X-StayOps-Demo-Token",
    ),
):
    if x_stayops_demo_token is None:
        raise HTTPException(
            status_code=401,
            detail="Demo session token is required.",
        )

    try:
        return validate_demo_session(
            x_stayops_demo_token
        )

    except DemoSessionExpired as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    except DemoSessionUnauthorized as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc


def require_demo_api_session(
    x_stayops_demo_token: str | None = Header(
        default=None,
        alias="X-StayOps-Demo-Token",
    ),
):
    if x_stayops_demo_token:
        return require_demo_session(
            x_stayops_demo_token
        )

    if os.getenv("STAYOPS_ALLOW_LEGACY_DEMO") == "1":
        return {
            "session_id": None,
            "legacy": True,
        }

    raise HTTPException(
        status_code=401,
        detail="Demo session token is required.",
    )


def require_legacy_demo_mode():
    if os.getenv("STAYOPS_ALLOW_LEGACY_DEMO") != "1":
        raise HTTPException(
            status_code=404,
            detail="Not found.",
        )


def _is_legacy_session(session: dict) -> bool:
    return bool(session.get("legacy"))


def _deny(exc: DemoSessionAccessDenied):
    raise HTTPException(
        status_code=403,
        detail=str(exc),
    ) from exc


def _authorize_booking(session: dict, booking_id: str):
    if _is_legacy_session(session):
        return
    try:
        require_demo_booking_access(
            session_id=session["session_id"],
            booking_id=booking_id,
        )
    except DemoSessionAccessDenied as exc:
        _deny(exc)


def _authorize_guest(session: dict, guest_id: str):
    if _is_legacy_session(session):
        return
    try:
        require_demo_guest_access(
            session_id=session["session_id"],
            guest_id=guest_id,
        )
    except DemoSessionAccessDenied as exc:
        _deny(exc)


def _authorize_case(session: dict, case_id: str):
    if _is_legacy_session(session):
        return
    try:
        require_demo_case_access(
            session_id=session["session_id"],
            case_id=case_id,
        )
    except DemoSessionAccessDenied as exc:
        _deny(exc)


def _authorize_task(session: dict, task_id: str):
    if _is_legacy_session(session):
        return
    try:
        require_demo_task_access(
            session_id=session["session_id"],
            task_id=task_id,
        )
    except DemoSessionAccessDenied as exc:
        _deny(exc)


def _authorize_escalation(session: dict, escalation_id: str):
    if _is_legacy_session(session):
        return
    try:
        require_demo_escalation_access(
            session_id=session["session_id"],
            escalation_id=escalation_id,
        )
    except DemoSessionAccessDenied as exc:
        _deny(exc)


def _authorize_compensation(session: dict, compensation_request_id: str):
    if _is_legacy_session(session):
        return
    try:
        require_demo_compensation_access(
            session_id=session["session_id"],
            compensation_request_id=compensation_request_id,
        )
    except DemoSessionAccessDenied as exc:
        _deny(exc)


def _authorize_incident(session: dict, incident_id: str):
    if _is_legacy_session(session):
        return
    try:
        require_demo_incident_access(
            session_id=session["session_id"],
            incident_id=incident_id,
        )
    except DemoSessionAccessDenied as exc:
        _deny(exc)


def _authorize_booking_and_guest(
    session: dict,
    *,
    booking_id: str,
    guest_id: str,
):
    _authorize_booking(session, booking_id)
    _authorize_guest(session, guest_id)

    reservation = get_reservation(booking_id)

    if reservation is None:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found.",
        )

    if reservation["guest_id"] != guest_id:
        raise HTTPException(
            status_code=403,
            detail="Guest does not belong to the supplied booking.",
        )


def _authorize_optional_booking(session: dict, booking_id: str | None):
    if _is_legacy_session(session):
        return

    if booking_id is None:
        raise HTTPException(
            status_code=403,
            detail="A session-owned booking is required.",
        )

    _authorize_booking(session, booking_id)


def _session_booking_ids(session: dict):
    if _is_legacy_session(session):
        return None
    return set(
        get_demo_session_booking_ids(
            session["session_id"]
        )
    )


def require_demo_booking_scope(
    booking_id: str,
    session=Depends(require_demo_api_session),
):
    _authorize_booking(session, booking_id)
    return session


def require_demo_guest_scope(
    guest_id: str,
    session=Depends(require_demo_api_session),
):
    _authorize_guest(session, guest_id)
    return session


def require_demo_case_scope(
    case_id: str,
    session=Depends(require_demo_api_session),
):
    _authorize_case(session, case_id)
    return session


def require_demo_task_scope(
    task_id: str,
    session=Depends(require_demo_api_session),
):
    _authorize_task(session, task_id)
    return session


def require_demo_escalation_scope(
    escalation_id: str,
    session=Depends(require_demo_api_session),
):
    _authorize_escalation(session, escalation_id)
    return session


def require_demo_compensation_scope(
    compensation_request_id: str,
    session=Depends(require_demo_api_session),
):
    _authorize_compensation(session, compensation_request_id)
    return session


def require_demo_incident_scope(
    incident_id: str,
    session=Depends(require_demo_api_session),
):
    _authorize_incident(session, incident_id)
    return session


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
def read_guest(
    guest_id: str,
    _session=Depends(require_demo_guest_scope),
):
    guest = get_guest(guest_id)

    if guest is None:
        raise HTTPException(
            status_code=404,
            detail="Guest not found",
        )

    return guest


@app.get("/guests/{guest_id}/reservations")
def read_guest_reservations(
    guest_id: str,
    _session=Depends(require_demo_guest_scope),
):
    return get_guest_reservations(guest_id)


# ---------------------------------------------------------
# RESERVATIONS
# ---------------------------------------------------------

@app.get("/reservations/{booking_id}")
def read_reservation(
    booking_id: str,
    _session=Depends(require_demo_booking_scope),
):
    reservation = get_reservation(booking_id)

    if reservation is None:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found",
        )

    return reservation



# ---------------------------------------------------------
# HUMAN OPERATIONS
# ---------------------------------------------------------

@app.get("/operations/queue")
def read_human_operations_queue(
    session=Depends(require_demo_api_session),
):
    queue = get_human_operations_queue()
    allowed = _session_booking_ids(session)
    if allowed is None:
        return queue
    return [
        entry for entry in queue
        if entry["case"]["booking_id"] in allowed
    ]


@app.get("/operations/technicians")
def read_maintenance_technicians():
    return get_maintenance_workers()



@app.patch("/cases/{case_id}/claim")
def claim_case_for_operator(
    case_id: str,
    payload: CaseOperatorAction,
    _session=Depends(require_demo_case_scope),
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
    _session=Depends(require_demo_case_scope),
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
def read_case(
    case_id: str,
    _session=Depends(require_demo_case_scope),
):
    case = get_case(case_id)

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return case

@app.get("/cases/{case_id}/timeline")
def read_case_timeline(
    case_id: str,
    _session=Depends(require_demo_case_scope),
):
    try:
        return get_case_timeline(case_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@app.get("/reservations/{booking_id}/cases")
def read_booking_cases(
    booking_id: str,
    _session=Depends(require_demo_booking_scope),
):
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
def read_open_incidents(
    property_id: str,
    session=Depends(require_demo_api_session),
):
    incidents = get_open_incidents(property_id)
    allowed = _session_booking_ids(session)
    if allowed is None:
        return incidents
    return [
        item
        for item in incidents
        if item["booking_id"] in allowed
    ]


@app.get("/properties/{property_id}/tasks")
def read_open_tasks(
    property_id: str,
    session=Depends(require_demo_api_session),
):
    tasks = get_open_tasks(property_id)
    allowed = _session_booking_ids(session)
    if allowed is None:
        return tasks
    return [
        item
        for item in tasks
        if item["booking_id"] in allowed
    ]


# ---------------------------------------------------------
# MESSAGES
# ---------------------------------------------------------

@app.post("/messages")
def create_message(
    payload: MessageCreate,
    session=Depends(require_demo_api_session),
):
    _authorize_booking_and_guest(
        session,
        booking_id=payload.booking_id,
        guest_id=payload.guest_id,
    )

    return send_message(
        booking_id=payload.booking_id,
        guest_id=payload.guest_id,
        sender_type=payload.sender_type,
        message_text=payload.message_text,
        channel=payload.channel,
    )

@app.get("/reservations/{booking_id}/messages")
def read_booking_messages(
    booking_id: str,
    _session=Depends(require_demo_booking_scope),
):
    return get_booking_messages(booking_id)

# ---------------------------------------------------------
# INCIDENTS
# ---------------------------------------------------------

@app.post("/incidents")
def create_new_incident(
    payload: IncidentCreate,
    session=Depends(require_demo_api_session),
):
    _authorize_optional_booking(
        session,
        payload.booking_id,
    )

    return create_incident(
        property_id=payload.property_id,
        booking_id=payload.booking_id,
        category=payload.category,
        description=payload.description,
        severity=payload.severity,
    )


@app.patch("/incidents/{incident_id}/resolve")
def resolve_existing_incident(
    incident_id: str,
    _session=Depends(require_demo_incident_scope),
):
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
def create_new_task(
    payload: TaskCreate,
    session=Depends(require_demo_api_session),
):
    _authorize_optional_booking(
        session,
        payload.booking_id,
    )

    return create_task(
        property_id=payload.property_id,
        booking_id=payload.booking_id,
        category=payload.category,
        title=payload.title,
        assigned_by=payload.assigned_by,
        assigned_to=payload.assigned_to,
        parent_task_id=payload.parent_task_id,
    )

@app.patch("/tasks/{task_id}/assign")
def assign_existing_task(
    task_id: str,
    payload: TaskAssignmentAction,
    _session=Depends(require_demo_task_scope),
):
    try:
        return assign_task(
            task_id=task_id,
            operator_id=payload.operator_id,
            worker_id=payload.worker_id,
        )

    except ValueError as exc:
        detail = str(exc)

        status_code = (
            404
            if (
                detail.startswith("Task does not exist:")
                or detail.startswith("Worker does not exist:")
                or detail.startswith("Case does not exist:")
            )
            else 409
        )

        raise HTTPException(
            status_code=status_code,
            detail=detail,
        )

@app.patch("/tasks/{task_id}/complete")
def complete_existing_task(
    task_id: str,
    payload: CaseOperatorAction,
    _session=Depends(require_demo_task_scope),
):
    try:
        task = complete_task(
            task_id=task_id,
            operator_id=payload.operator_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

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
def create_new_escalation(
    payload: EscalationCreate,
    session=Depends(require_demo_api_session),
):
    _authorize_optional_booking(
        session,
        payload.booking_id,
    )

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
def read_open_escalations(
    session=Depends(require_demo_api_session),
):
    escalations = get_open_escalations()
    allowed = _session_booking_ids(session)
    if allowed is None:
        return escalations
    return [
        item
        for item in escalations
        if item["booking_id"] in allowed
    ]


@app.get("/access/verify")
def verify_access(
    guest_id: str,
    booking_id: str,
    session=Depends(require_demo_api_session),
):
    _authorize_booking_and_guest(
        session,
        booking_id=booking_id,
        guest_id=guest_id,
    )

    return verify_guest_access(
        guest_id=guest_id,
        booking_id=booking_id,
    )

@app.patch("/escalations/{escalation_id}/resolve")
def resolve_existing_escalation(
    escalation_id: str,
    payload: CaseOperatorAction,
    _session=Depends(require_demo_escalation_scope),
):
    try:
        escalation = resolve_escalation(
            escalation_id=escalation_id,
            operator_id=payload.operator_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

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
    _session=Depends(require_demo_compensation_scope),
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
    _session=Depends(require_demo_compensation_scope),
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
async def agent_chat(
    payload: AgentChatRequest,
    session=Depends(require_demo_api_session),
):
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

    _authorize_booking_and_guest(
        session,
        booking_id=payload.booking_id,
        guest_id=payload.guest_id,
    )

    try:
        # -----------------------------------------------------
        # LOAD EXISTING MULTI-TURN CONTEXT
        # -----------------------------------------------------

        guest = get_guest(
            payload.guest_id
        )

        reservation = get_reservation(
            payload.booking_id
        )

        property_data = None

        if reservation is not None:
            property_id = reservation.get(
                "property_id"
            )

            if property_id:
                property_data = get_property(
                    property_id
                )

        open_cases = get_open_cases_for_booking(
            payload.booking_id
        )

        recent_cases = get_recent_cases_for_booking(
            payload.booking_id,
            limit=5,
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
            recent_cases=recent_cases,
            recent_messages=recent_messages,
            mcp_servers=app.state.mcp_servers,
            guest=guest,
            reservation=reservation,
            property_data=property_data,
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
            "ensure_refund_workflow": "Refund workflow created or reused",
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

@app.post(
    "/demo/sessions",
    status_code=201,
)
def create_public_demo_session():
    return create_demo_session()


@app.get("/demo/sessions/current")
def read_public_demo_session(
    session=Depends(
        require_demo_session
    ),
):
    return {
        "session_id": session["session_id"],
        "created_at": session["created_at"],
        "last_seen_at": session["last_seen_at"],
        "expires_at": session["expires_at"],
    }


@app.get("/demo/sessions/stays")
def read_public_demo_session_stays(
    session=Depends(
        require_demo_session
    ),
):
    return get_demo_session_stays(
        session["session_id"]
    )


@app.post(
    "/demo/sessions/stays",
    status_code=201,
)
def create_public_demo_session_stay(
    payload: DemoGuestStayCreate,
    session=Depends(
        require_demo_session
    ),
):
    try:
        return create_demo_guest_stay(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            guest_lang=payload.guest_lang,
            property_id=payload.property_id,
            session_id=session["session_id"],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.get("/demo/stays")
def read_demo_stays(
    _legacy=Depends(require_legacy_demo_mode),
):
    return get_demo_stays()


@app.get("/demo/properties")
def read_demo_properties():
    return get_demo_properties()


@app.post(
    "/demo/stays",
    status_code=201,
)
def create_demo_stay(
    payload: DemoGuestStayCreate,
    _legacy=Depends(require_legacy_demo_mode),
):
    try:
        return create_demo_guest_stay(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            guest_lang=payload.guest_lang,
            property_id=payload.property_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post("/demo/reset/{booking_id}")
def reset_demo(
    booking_id: str,
    _session=Depends(require_demo_booking_scope),
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