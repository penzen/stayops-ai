from fastapi import FastAPI, HTTPException
from backend.services.access_rules import verify_guest_access
from backend.domain.enums import SenderType
from fastapi.middleware.cors import CORSMiddleware
from backend.services.demo import (
    get_demo_stays,
    reset_demo_state,
)

from backend.api.schemas import (
    MessageCreate,
    IncidentCreate,
    TaskCreate,
    EscalationCreate,
    AgentChatRequest,
    AgentChatResponse,
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
)

from backend.services.escalations import (
    create_escalation,
    get_open_escalations,
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
        # Persist the incoming guest message deterministically.
        send_message(
            booking_id=payload.booking_id,
            guest_id=payload.guest_id,
            sender_type=SenderType.GUEST,
            message_text=payload.message,
        )

        result = await run_guest_agent(
            guest_id=payload.guest_id,
            booking_id=payload.booking_id,
            message=payload.message,
            scenario_name="api_guest_chat",
            show_tools=False,
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