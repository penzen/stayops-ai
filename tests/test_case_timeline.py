from backend.services.cases import (
    ensure_case,
    transition_case_status,
    claim_case,
    return_case_to_agent,
    resolve_case_if_ready,
)

from backend.services.audit import (
    record_case_event,
    get_case_timeline,
)

from fastapi.testclient import TestClient
from backend.api.main import app

from backend.services.tasks import (
    create_task_if_missing,
    complete_task,
)

from backend.services.escalations import (
    create_escalation_if_missing,
    resolve_escalation,
)

from backend.services.compensation import (
    ensure_compensation_request,
    record_compensation_decision,
)


client = TestClient(app)
PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"
OPERATOR_ID = "GRO_254"


def test_case_event_can_be_recorded_and_retrieved(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure.",
    )

    case_id = case_result["case"]["case_id"]

    event = record_case_event(
        case_id=case_id,
        event_type="case_claimed",
        actor_type="human",
        actor_id=OPERATOR_ID,
        summary="Operator claimed the Case.",
        metadata={
            "operator_id": OPERATOR_ID,
        },
    )

    assert event["case_id"] == case_id
    assert event["event_type"] == "case_claimed"
    assert event["actor_type"] == "human"
    assert event["actor_id"] == OPERATOR_ID
    assert event["summary"] == "Operator claimed the Case."

    assert event["metadata"] == {
        "operator_id": OPERATOR_ID,
    }

    assert event["created_at"] is not None

    timeline = get_case_timeline(
        case_id
    )

    matching_event = next(
        item
        for item in timeline
        if item["case_event_id"]
        == event["case_event_id"]
    )

    assert matching_event == event

def test_case_lifecycle_is_automatically_audited(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure.",
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

    return_case_to_agent(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    timeline = get_case_timeline(
        case_id
    )

    event_types = [
        event["event_type"]
        for event in timeline
    ]

    assert event_types == [
        "case_created",
        "case_status_changed",
        "case_claimed",
        "case_returned_to_agent",
    ]

    claim_event = timeline[2]

    assert claim_event["actor_type"] == "human"
    assert claim_event["actor_id"] == OPERATOR_ID

    return_event = timeline[3]

    assert (
        return_event["metadata"]["to_status"]
        == "in_progress"
    )


def test_case_resolution_is_audited(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
        case_id=case_id,
    )

    complete_task(
        task_result["task"]["task_id"]
    )

    resolution = resolve_case_if_ready(
        case_id
    )

    assert resolution["resolved"] is True

    timeline = get_case_timeline(
        case_id
    )

    assert timeline[-1]["event_type"] == "case_resolved"

    assert (
        timeline[-1]["metadata"]["to_status"]
        == "resolved"
    )

def test_task_lifecycle_is_audited(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
        case_id=case_id,
    )

    task_id = task_result["task"]["task_id"]

    complete_task(
        task_id
    )

    timeline = get_case_timeline(
        case_id
    )

    event_types = [
        event["event_type"]
        for event in timeline
    ]

    assert event_types == [
        "case_created",
        "task_created",
        "task_completed",
    ]

    assert (
        timeline[1]["metadata"]["task_id"]
        == task_id
    )

    assert (
        timeline[2]["metadata"]["task_id"]
        == task_id
    )

def test_escalation_lifecycle_is_audited(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Active plumbing leak.",
    )

    case_id = case_result["case"]["case_id"]

    escalation_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Physical intervention required.",
        priority="high",
        case_id=case_id,
    )

    escalation_id = (
        escalation_result[
            "escalation"
        ]["escalation_id"]
    )

    resolve_escalation(
        escalation_id
    )

    timeline = get_case_timeline(
        case_id
    )

    event_types = [
        event["event_type"]
        for event in timeline
    ]

    assert event_types == [
        "case_created",
        "escalation_created",
        "escalation_resolved",
    ]

    assert (
        timeline[1]["metadata"]["escalation_id"]
        == escalation_id
    )

    assert (
        timeline[2]["metadata"]["escalation_id"]
        == escalation_id
    )

def test_compensation_workflow_is_audited(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    case_id = case_result["case"]["case_id"]

    request_result = ensure_compensation_request(
        case_id=case_id,
        reason="Heating failure affected the stay.",
        requested_outcome="Partial refund",
    )

    compensation_request_id = (
        request_result[
            "compensation_request"
        ]["compensation_request_id"]
    )

    transition_case_status(
    case_id=case_id,
    new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    decision_result = record_compensation_decision(
        compensation_request_id=compensation_request_id,
        decision="approved",
        decided_by=OPERATOR_ID,
        reason="Service disruption confirmed.",
        amount=150.0,
        currency="EUR",
    )

    assert decision_result["created"] is True

    timeline = get_case_timeline(
        case_id
    )

    event_types = [
        event["event_type"]
        for event in timeline
    ]

    assert event_types == [
        "case_created",
        "compensation_review_created",
        "case_status_changed",
        "case_claimed",
        "compensation_decision_recorded",
    ]

    review_event = timeline[1]

    assert (
        review_event["metadata"][
            "compensation_request_id"
        ]
        == compensation_request_id
    )

    decision_event = next(
    event
    for event in timeline
    if event["event_type"]
    == "compensation_decision_recorded"
)

    assert decision_event["actor_type"] == "human"
    assert decision_event["actor_id"] == OPERATOR_ID

    assert (
        decision_event["metadata"]["decision"]
        == "approved"
    )

    assert (
        decision_event["metadata"]["amount"]
        == 150.0
    )

    assert (
        decision_event["metadata"]["currency"]
        == "EUR"
    )

def test_repeated_compensation_decision_does_not_duplicate_audit_event(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    case_id = case_result["case"]["case_id"]

    request_result = ensure_compensation_request(
        case_id=case_id,
        reason="Heating failure.",
        requested_outcome="Partial refund",
    )

    compensation_request_id = (
        request_result[
            "compensation_request"
        ]["compensation_request_id"]
    )

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    claim_case(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    for _ in range(2):
        record_compensation_decision(
            compensation_request_id=
                compensation_request_id,
            decision="approved",
            decided_by=OPERATOR_ID,
            reason="Service disruption confirmed.",
            amount=150.0,
            currency="EUR",
        )

    timeline = get_case_timeline(
        case_id
    )

    decision_events = [
        event
        for event in timeline
        if event["event_type"]
        == "compensation_decision_recorded"
    ]

    assert len(decision_events) == 1

def test_case_timeline_endpoint(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failure.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    response = client.get(
        f"/cases/{case_id}/timeline"
    )

    assert response.status_code == 200

    timeline = response.json()

    assert len(timeline) == 2

    assert timeline[0]["event_type"] == "case_created"
    assert (
        timeline[1]["event_type"]
        == "case_status_changed"
    )

def test_case_timeline_endpoint_returns_404_for_missing_case(
    test_db,
):
    response = client.get(
        "/cases/case_does_not_exist/timeline"
    )

    assert response.status_code == 404


def test_full_handoff_timeline_is_visible_through_api(
    test_db,
):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported an active plumbing leak.",
    )

    case_id = case_result["case"]["case_id"]

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

    return_case_to_agent(
        case_id=case_id,
        operator_id=OPERATOR_ID,
    )

    response = client.get(
        f"/cases/{case_id}/timeline"
    )

    assert response.status_code == 200

    timeline = response.json()

    event_types = [
        event["event_type"]
        for event in timeline
    ]

    assert event_types == [
        "case_created",
        "task_created",
        "escalation_created",
        "case_status_changed",
        "case_claimed",
        "task_completed",
        "escalation_resolved",
        "case_returned_to_agent",
    ]

    assert (
        timeline[4]["actor_id"]
        == OPERATOR_ID
    )

    assert (
        timeline[-1]["event_type"]
        == "case_returned_to_agent"
    )