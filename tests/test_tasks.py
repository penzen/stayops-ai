from backend.services.tasks import (
    create_task_if_missing,
    assign_task,
)

from backend.services.cases import (
    ensure_case,
    transition_case_status,
    claim_case,
)

from backend.services.audit import (
    get_case_timeline,
)

from fastapi.testclient import TestClient

from backend.api.main import app

OPERATOR_ID = "GRO_254"
WORKER_ID = "MNT_683"

PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"
client = TestClient(app)

def test_create_task_if_missing_reuses_existing_task(test_db):
    first_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
    )

    second_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure again",
    )

    assert first_result["created"] is True
    assert first_result["reason"] == "task_created"

    assert second_result["created"] is False
    assert second_result["reason"] == "existing_open_task"

    assert (
        first_result["task"]["task_id"]
        == second_result["task"]["task_id"]
    )

def test_claimed_case_task_can_be_assigned_to_maintenance_worker(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure requires technician intervention.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Inspect and restore heating",
        case_id=case_id,
    )

    task_id = task_result["task"]["task_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    result = assign_task(
        task_id=task_id,
        operator_id=OPERATOR_ID,
        worker_id=WORKER_ID,
    )

    assert result["assigned"] is True
    assert result["reason"] == "task_assigned"

    assert (
        result["task"]["assigned_to"]
        == WORKER_ID
    )

    assert (
        result["worker"]["team_id"]
        == WORKER_ID
    )

    assert (
        result["worker"]["team_group"]
        == "technical_maintenance"
    )

    timeline = get_case_timeline(
        case_id
    )

    assignment_events = [
        event
        for event in timeline
        if event["event_type"]
        == "task_assigned"
    ]

    assert len(assignment_events) == 1

    assert (
        assignment_events[0]["actor_id"]
        == OPERATOR_ID
    )

    assert (
        assignment_events[0]["metadata"]["worker_id"]
        == WORKER_ID
    )

def test_task_assignment_endpoint(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure requires technician intervention.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Inspect and restore heating",
        case_id=case_id,
    )

    task_id = task_result["task"]["task_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    response = client.patch(
        f"/tasks/{task_id}/assign",
        json={
            "operator_id": OPERATOR_ID,
            "worker_id": WORKER_ID,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["assigned"] is True
    assert data["reason"] == "task_assigned"

    assert (
        data["task"]["assigned_to"]
        == WORKER_ID
    )

    assert (
        data["worker"]["team_id"]
        == WORKER_ID
    )

    timeline = get_case_timeline(
        case_id
    )

    assignment_events = [
        event
        for event in timeline
        if event["event_type"]
        == "task_assigned"
    ]

    assert len(assignment_events) == 1
"""
First request
    ↓
No matching open heating task
    ↓
CREATE TASK
    ↓
created = True

Second request
    ↓
Matching open heating task exists
    ↓
REUSE TASK
    ↓
created = False
    ↓
same task_id ✓
    
    
"""