from backend.services.cases import (
    ensure_case,
    transition_case_status,
    claim_case,
    get_human_operations_queue,
    return_case_to_agent,
)
import pytest
from backend.services.cases import (
    ensure_case,
    transition_case_status,
    claim_case,
    get_human_operations_queue,
)

from backend.services.tasks import (
    create_task_if_missing,
    complete_task,
)

from backend.services.escalations import (
    create_escalation_if_missing,
    resolve_escalation,
)
from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)

PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"
OPERATOR_ID = "GRO_254"


def test_waiting_human_case_can_be_claimed(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    result = claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    assert result["claimed"] is True
    assert result["reason"] == "case_claimed"

    case = result["case"]

    assert case["case_id"] == case_id
    assert case["status"] == "waiting_human"
    assert case["assigned_to"] == OPERATOR_ID
    assert case["claimed_at"] is not None




def test_case_cannot_be_claimed_unless_waiting_human(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating issue still being handled autonomously.",
    )

    case_id = case_result["case"]["case_id"]

    with pytest.raises(
        ValueError,
        match="Case must be waiting_human",
    ):
        claim_case(
            case_id=case_id,
            operator_id=OPERATOR_ID,
        )


def test_claimed_case_cannot_be_stolen_by_another_operator(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    with pytest.raises(
        ValueError,
        match="already claimed",
    ):
        claim_case(
            case_id=case_id,
            operator_id="GRO_612",
        )

def test_same_operator_claim_is_idempotent(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    first = claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    second = claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    assert first["claimed"] is True

    assert second["claimed"] is False
    assert (
        second["reason"]
        == "already_claimed_by_operator"
    )

    assert (
        second["case"]["assigned_to"]
        == OPERATOR_ID
    )

    assert (
        second["case"]["claimed_at"]
        == first["case"]["claimed_at"]
    )

def test_human_operations_queue_returns_waiting_human_case(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
        case_id=case_id,
    )

    create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Guest has no functioning heating.",
        priority="high",
        case_id=case_id,
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    queue = get_human_operations_queue()

    entry = next(
        item
        for item in queue
        if item["case"]["case_id"] == case_id
    )

    assert entry["case"]["status"] == "waiting_human"
    assert entry["case"]["assigned_to"] == OPERATOR_ID

    assert entry["booking"]["booking_id"] == BOOKING_ID
    assert entry["guest"]["guest_id"] == "gst_2631"
    assert entry["property"]["property_id"] == PROPERTY_ID

    assert len(entry["tasks"]) == 1
    assert len(entry["escalations"]) == 1

    assert (
        entry["handoff"]["reason"]
        == "Guest has no functioning heating."
    )

    assert entry["handoff"]["priority"] == "high"

    assert (
        entry["operator"]["team_id"]
        == OPERATOR_ID
    )

def test_unclaimed_waiting_human_case_appears_in_queue(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Leak requires human assistance.",
    )

    case_id = case_result["case"]["case_id"]

    create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Plumber intervention required.",
        priority="high",
        case_id=case_id,
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    queue = get_human_operations_queue()

    entry = next(
        item
        for item in queue
        if item["case"]["case_id"] == case_id
    )

    assert entry["case"]["assigned_to"] is None
    assert entry["operator"] is None
    assert entry["handoff"]["claimed_at"] is None


def test_non_waiting_human_case_does_not_appear_in_queue(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating issue handled autonomously.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="in_progress",
    )

    queue = get_human_operations_queue()

    queue_case_ids = {
        item["case"]["case_id"]
        for item in queue
    }

    assert case_id not in queue_case_ids


def test_human_operations_queue_endpoint(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Human heating intervention required.",
        priority="high",
        case_id=case_id,
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    response = client.get(
        "/operations/queue"
    )

    assert response.status_code == 200

    data = response.json()

    entry = next(
        item
        for item in data
        if item["case"]["case_id"] == case_id
    )

    assert entry["case"]["status"] == "waiting_human"
    assert (
        entry["handoff"]["reason"]
        == "Human heating intervention required."
    )

def test_claimed_case_can_return_to_agent_after_human_work(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
        case_id=case_id,
    )

    escalation_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Human heating intervention required.",
        priority="high",
        case_id=case_id,
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    complete_task(
        task_result["task"]["task_id"]
    )

    resolve_escalation(
        escalation_result[
            "escalation"
        ]["escalation_id"]
    )

    result = return_case_to_agent(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    assert result["returned"] is True
    assert result["reason"] == "case_returned_to_agent"

    case = result["case"]

    assert case["status"] == "in_progress"
    assert case["assigned_to"] is None
    assert case["claimed_at"] is None

def test_case_cannot_return_to_agent_with_open_human_work(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Plumbing issue requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="plumbing",
        title="Repair leaking plumbing",
        case_id=case_id,
    )

    create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Physical repair required.",
        priority="high",
        case_id=case_id,
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    with pytest.raises(
        ValueError,
        match="open human work",
    ):
        return_case_to_agent(
            case_id=case_id,
            operator_id=OPERATOR_ID,
        )


def test_only_current_operator_can_return_case_to_agent(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating issue requires human review.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    with pytest.raises(
        ValueError,
        match="assigned operator",
    ):
        return_case_to_agent(
            case_id=case_id,
            operator_id="GRO_612",
        )


def test_claim_case_endpoint(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    response = client.patch(
        f"/cases/{case_id}/claim",
        json={
            "operator_id": OPERATOR_ID,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["claimed"] is True
    assert data["case"]["assigned_to"] == OPERATOR_ID
    assert data["case"]["status"] == "waiting_human"


def test_return_case_to_agent_endpoint(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    response = client.patch(
        f"/cases/{case_id}/return-to-agent",
        json={
            "operator_id": OPERATOR_ID,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["returned"] is True
    assert data["case"]["status"] == "in_progress"
    assert data["case"]["assigned_to"] is None

def test_full_agent_human_agent_handoff_lifecycle(test_db):
    # Agent-owned operational Case.
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported an active plumbing leak.",
    )

    case_id = case_result["case"]["case_id"]

    # Agent creates operational work.
    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="plumbing",
        title="Investigate plumbing leak",
        case_id=case_id,
    )

    escalation_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Physical plumbing intervention required.",
        priority="high",
        case_id=case_id,
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    # -----------------------------------------------------
    # HUMAN QUEUE
    # -----------------------------------------------------

    queue_response = client.get(
        "/operations/queue"
    )

    assert queue_response.status_code == 200

    queue = queue_response.json()

    queued_case = next(
        item
        for item in queue
        if item["case"]["case_id"] == case_id
    )

    assert queued_case["operator"] is None

    # -----------------------------------------------------
    # HUMAN CLAIM
    # -----------------------------------------------------

    claim_response = client.patch(
        f"/cases/{case_id}/claim",
        json={
            "operator_id": OPERATOR_ID,
        },
    )

    assert claim_response.status_code == 200
    assert (
        claim_response.json()["case"]["assigned_to"]
        == OPERATOR_ID
    )

    # -----------------------------------------------------
    # HUMAN COMPLETES BLOCKING WORK
    # -----------------------------------------------------

    task_id = task_result["task"]["task_id"]

    task_response = client.patch(
        f"/tasks/{task_id}/complete",
        json={
            "operator_id": OPERATOR_ID,
        },
    )

    assert task_response.status_code == 200

    escalation_id = (
        escalation_result[
            "escalation"
        ]["escalation_id"]
    )

    escalation_response = client.patch(
    f"/escalations/{escalation_id}/resolve",
    json={
        "operator_id": OPERATOR_ID,
        },
    )

    assert escalation_response.status_code == 200

    # -----------------------------------------------------
    # HUMAN RETURNS CONTROL
    # -----------------------------------------------------

    return_response = client.patch(
        f"/cases/{case_id}/return-to-agent",
        json={
            "operator_id": OPERATOR_ID,
        },
    )

    assert return_response.status_code == 200

    returned_case = return_response.json()["case"]

    assert returned_case["status"] == "in_progress"
    assert returned_case["assigned_to"] is None
    assert returned_case["claimed_at"] is None

    # -----------------------------------------------------
    # CASE LEAVES HUMAN QUEUE
    # -----------------------------------------------------

    final_queue = client.get(
        "/operations/queue"
    ).json()

    queue_case_ids = {
        entry["case"]["case_id"]
        for entry in final_queue
    }

    assert case_id not in queue_case_ids


def test_unclaimed_case_cannot_return_to_agent(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    with pytest.raises(
        ValueError,
        match="must be claimed",
    ):
        return_case_to_agent(
            case_id=case_id,
            operator_id=OPERATOR_ID,
        )

def test_assigned_operator_can_complete_case_task(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating requires human work.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Restore heating",
        case_id=case_id,
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    task = complete_task(
        task_id=task_result["task"]["task_id"],
        operator_id=OPERATOR_ID,
    )

    assert task["task_status"] == "completed"

def test_other_operator_cannot_complete_case_task(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating requires human work.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Restore heating",
        case_id=case_id,
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    with pytest.raises(
        ValueError,
        match="assigned Case operator",
    ):
        complete_task(
            task_id=task_result["task"]["task_id"],
            operator_id="GRO_612",
        )

def test_assigned_operator_can_resolve_case_escalation(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Plumbing requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    escalation_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Physical plumbing work required.",
        priority="high",
        case_id=case_id,
    )

    escalation_id = (
        escalation_result[
            "escalation"
        ]["escalation_id"]
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    escalation = resolve_escalation(
        escalation_id=escalation_id,
        operator_id=OPERATOR_ID,
    )

    assert escalation["status"] == "resolved"


def test_other_operator_cannot_resolve_case_escalation(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Plumbing requires human intervention.",
    )

    case_id = case_result["case"]["case_id"]

    escalation_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Physical plumbing work required.",
        priority="high",
        case_id=case_id,
    )

    escalation_id = (
        escalation_result[
            "escalation"
        ]["escalation_id"]
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    with pytest.raises(
        ValueError,
        match="assigned Case operator",
    ):
        resolve_escalation(
            escalation_id=escalation_id,
            operator_id="GRO_612",
        )