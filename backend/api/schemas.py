from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    booking_id: str
    guest_id: str
    sender_type: str = "agent"
    message_text: str
    channel: str = "chat"


class IncidentCreate(BaseModel):
    property_id: str
    booking_id: str | None = None
    category: str
    description: str
    severity: str = "medium"


class TaskCreate(BaseModel):
    property_id: str
    booking_id: str | None = None
    category: str
    title: str
    assigned_by: str = "AI_AGENT"
    assigned_to: str | None = None
    parent_task_id: str | None = None


class EscalationCreate(BaseModel):
    booking_id: str | None = None
    property_id: str
    incident_id: str | None = None
    reason: str
    priority: str = "medium"
    assigned_to: str | None = None
    category: str

class AgentChatRequest(BaseModel):
    guest_id: str
    booking_id: str
    message: str

class AgentChatResponse(BaseModel):
    guest_id: str
    booking_id: str
    response: str
    activities: list[str]

"""
These define what JSON FastAPI expects for write operations.

For example:

{
  "property_id": "prop_15",
  "booking_id": "book_0014",
  "category": "access",
  "description": "Guest cannot enter apartment",
  "severity": "high"
}


"""