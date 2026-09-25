import uuid

from backend.services.db import get_connection


def get_compensation_request_by_case(
    case_id: str,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM compensation_requests
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def ensure_compensation_request(
    case_id: str,
    reason: str,
    requested_outcome: str | None = None,
    related_case_id: str | None = None,
):
    """
    Ensure that one compensation request exists for a refund Case.

    The refund Case owns the financial workflow.

    related_case_id may reference the operational Case that caused
    the compensation request, such as a heating or plumbing Case.
    """

    connection = get_connection()

    try:
        # -----------------------------------------------------
        # VALIDATE REFUND CASE
        # -----------------------------------------------------

        refund_case_row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if refund_case_row is None:
            raise ValueError(
                f"Case does not exist: {case_id}"
            )

        refund_case = dict(refund_case_row)

        if refund_case["category"] != "refund":
            raise ValueError(
                "Compensation requests must belong to a refund Case."
            )

        # -----------------------------------------------------
        # IDEMPOTENT REUSE
        # -----------------------------------------------------

        existing_row = connection.execute(
            """
            SELECT *
            FROM compensation_requests
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if existing_row is not None:
            return {
                "created": False,
                "reason": "existing_compensation_request",
                "compensation_request": dict(
                    existing_row
                ),
            }

        # -----------------------------------------------------
        # VALIDATE RELATED OPERATIONAL CASE
        # -----------------------------------------------------

        if related_case_id is not None:
            related_case_row = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE case_id = ?
                """,
                (related_case_id,),
            ).fetchone()

            if related_case_row is None:
                raise ValueError(
                    "Related Case does not exist: "
                    f"{related_case_id}"
                )

            related_case = dict(
                related_case_row
            )

            if (
                related_case["booking_id"]
                != refund_case["booking_id"]
            ):
                raise ValueError(
                    "Related Case must belong to the same booking."
                )

            if (
                related_case["property_id"]
                != refund_case["property_id"]
            ):
                raise ValueError(
                    "Related Case must belong to the same property."
                )

        # -----------------------------------------------------
        # CREATE REQUEST
        # -----------------------------------------------------

        compensation_request_id = (
            "comp_"
            + uuid.uuid4().hex[:12]
        )

        connection.execute(
            """
            INSERT INTO compensation_requests (
                compensation_request_id,
                case_id,
                related_case_id,
                booking_id,
                property_id,
                reason,
                requested_outcome,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                compensation_request_id,
                case_id,
                related_case_id,
                refund_case["booking_id"],
                refund_case["property_id"],
                reason,
                requested_outcome,
                "pending_review",
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM compensation_requests
            WHERE compensation_request_id = ?
            """,
            (compensation_request_id,),
        ).fetchone()

        return {
            "created": True,
            "reason": "compensation_request_created",
            "compensation_request": dict(
                row
            ),
        }

    finally:
        connection.close()

def get_compensation_decision(
    compensation_request_id: str,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM compensation_decisions
            WHERE compensation_request_id = ?
            """,
            (compensation_request_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def record_compensation_decision(
    compensation_request_id: str,
    decision: str,
    decided_by: str,
    reason: str,
    amount: float | None = None,
    currency: str | None = None,
):
    """
    Record the final human decision for a compensation request.

    Financial decisions are final and may only be approved
    or denied.

    Approved decisions require an amount and currency.
    Denied decisions cannot include an amount.
    """

    normalized_decision = (
        decision.strip().lower()
    )

    allowed_decisions = {
        "approved",
        "denied",
    }

    if normalized_decision not in allowed_decisions:
        raise ValueError(
            "Invalid compensation decision. "
            "Allowed decisions: approved, denied."
        )

    if not decided_by.strip():
        raise ValueError(
            "decided_by is required."
        )

    if not reason.strip():
        raise ValueError(
            "Decision reason is required."
        )

    # -----------------------------------------------------
    # VALIDATE DECISION RULES
    # -----------------------------------------------------

    if normalized_decision == "approved":
        if amount is None:
            raise ValueError(
                "Approved compensation decisions "
                "require an amount."
            )

        if amount <= 0:
            raise ValueError(
                "Approved compensation amount "
                "must be greater than zero."
            )

        if currency is None or not currency.strip():
            raise ValueError(
                "Approved compensation decisions "
                "require a currency."
            )

        currency = currency.strip().upper()

    if normalized_decision == "denied":
        if amount is not None:
            raise ValueError(
                "Denied compensation decisions "
                "cannot include an amount."
            )

        amount = None
        currency = None

    connection = get_connection()

    try:
        # -------------------------------------------------
        # VALIDATE COMPENSATION REQUEST
        # -------------------------------------------------

        request_row = connection.execute(
            """
            SELECT *
            FROM compensation_requests
            WHERE compensation_request_id = ?
            """,
            (compensation_request_id,),
        ).fetchone()

        if request_row is None:
            raise ValueError(
                "Compensation request does not exist: "
                f"{compensation_request_id}"
            )

        # -------------------------------------------------
        # FINAL DECISIONS ARE IDEMPOTENT
        # -------------------------------------------------

        existing_row = connection.execute(
            """
            SELECT *
            FROM compensation_decisions
            WHERE compensation_request_id = ?
            """,
            (compensation_request_id,),
        ).fetchone()

        if existing_row is not None:
            return {
                "created": False,
                "reason": "existing_compensation_decision",
                "decision": dict(existing_row),
            }

        # -------------------------------------------------
        # CREATE FINAL DECISION
        # -------------------------------------------------

        compensation_decision_id = (
            "comp_dec_"
            + uuid.uuid4().hex[:12]
        )

        connection.execute(
            """
            INSERT INTO compensation_decisions (
                compensation_decision_id,
                compensation_request_id,
                decision,
                amount,
                currency,
                reason,
                decided_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                compensation_decision_id,
                compensation_request_id,
                normalized_decision,
                amount,
                currency,
                reason,
                decided_by,
            ),
        )

        # The request itself now reflects its final state.
        connection.execute(
            """
            UPDATE compensation_requests
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE compensation_request_id = ?
            """,
            (
                normalized_decision,
                compensation_request_id,
            ),
        )

        connection.commit()

        decision_row = connection.execute(
            """
            SELECT *
            FROM compensation_decisions
            WHERE compensation_decision_id = ?
            """,
            (compensation_decision_id,),
        ).fetchone()

        return {
            "created": True,
            "reason": "compensation_decision_recorded",
            "decision": dict(decision_row),
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_compensation_evidence(
    compensation_request_id: str,
):
    """
    Build a deterministic evidence package for a compensation
    request.

    This does not make a financial decision. It only gathers
    the operational facts that a human reviewer may use.
    """

    connection = get_connection()

    try:
        # -------------------------------------------------
        # COMPENSATION REQUEST
        # -------------------------------------------------

        request_row = connection.execute(
            """
            SELECT *
            FROM compensation_requests
            WHERE compensation_request_id = ?
            """,
            (compensation_request_id,),
        ).fetchone()

        if request_row is None:
            raise ValueError(
                "Compensation request does not exist: "
                f"{compensation_request_id}"
            )

        compensation_request = dict(request_row)

        # -------------------------------------------------
        # REFUND CASE
        # -------------------------------------------------

        refund_case_row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (
                compensation_request["case_id"],
            ),
        ).fetchone()

        refund_case = (
            dict(refund_case_row)
            if refund_case_row is not None
            else None
        )

        # -------------------------------------------------
        # BOOKING
        # -------------------------------------------------

        booking_row = connection.execute(
            """
            SELECT *
            FROM bookings
            WHERE booking_id = ?
            """,
            (
                compensation_request["booking_id"],
            ),
        ).fetchone()

        booking = (
            dict(booking_row)
            if booking_row is not None
            else None
        )

        # -------------------------------------------------
        # RELATED OPERATIONAL CASE
        # -------------------------------------------------

        related_case = None
        tasks = []
        escalations = []

        related_case_id = compensation_request[
            "related_case_id"
        ]

        if related_case_id is not None:
            related_case_row = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE case_id = ?
                """,
                (related_case_id,),
            ).fetchone()

            if related_case_row is not None:
                related_case = dict(
                    related_case_row
                )

                task_rows = connection.execute(
                    """
                    SELECT *
                    FROM tasks
                    WHERE case_id = ?
                    ORDER BY task_date ASC
                    """,
                    (related_case_id,),
                ).fetchall()

                tasks = [
                    dict(row)
                    for row in task_rows
                ]

                escalation_rows = connection.execute(
                    """
                    SELECT *
                    FROM escalations
                    WHERE case_id = ?
                    ORDER BY created_at ASC
                    """,
                    (related_case_id,),
                ).fetchall()

                escalations = [
                    dict(row)
                    for row in escalation_rows
                ]

        # -------------------------------------------------
        # OPERATIONAL COUNTS
        # -------------------------------------------------

        open_task_count = sum(
            1
            for task in tasks
            if task["task_status"] == "open"
        )

        open_escalation_count = sum(
            1
            for escalation in escalations
            if escalation["status"] == "open"
        )

        operational_evidence = {
            "task_count": len(tasks),
            "escalation_count": len(
                escalations
            ),
            "open_task_count":
                open_task_count,
            "open_escalation_count":
                open_escalation_count,
            "tasks": tasks,
            "escalations": escalations,
        }

        # -------------------------------------------------
        # HUMAN FINANCIAL DECISION
        # -------------------------------------------------

        decision_row = connection.execute(
            """
            SELECT *
            FROM compensation_decisions
            WHERE compensation_request_id = ?
            """,
            (compensation_request_id,),
        ).fetchone()

        decision = (
            dict(decision_row)
            if decision_row is not None
            else None
        )

        return {
            "compensation_request":
                compensation_request,
            "refund_case":
                refund_case,
            "related_case":
                related_case,
            "booking":
                booking,
            "operational_evidence":
                operational_evidence,
            "decision":
                decision,
        }

    finally:
        connection.close()


def build_compensation_assessment(
    compensation_request_id: str,
):
    """
    Build a deterministic compensation assessment from
    operational evidence.

    This assessment does not approve, deny, or assign a
    monetary amount. Final financial authority remains human.
    """

    evidence = get_compensation_evidence(
        compensation_request_id
    )

    related_case = evidence["related_case"]

    operational = evidence[
        "operational_evidence"
    ]

    factors = []

    # -----------------------------------------------------
    # OPERATIONAL EVIDENCE AVAILABILITY
    # -----------------------------------------------------

    operational_evidence_available = (
        related_case is not None
    )

    if not operational_evidence_available:
        factors.append(
            "missing_operational_evidence"
        )

        return {
            "compensation_request_id":
                compensation_request_id,
            "severity": "unknown",
            "operational_evidence_available": False,
            "operational_work_open": False,
            "human_review_required": True,
            "factors": factors,
        }

    # -----------------------------------------------------
    # OPEN OPERATIONAL WORK
    # -----------------------------------------------------

    operational_work_open = (
        operational["open_task_count"] > 0
        or operational[
            "open_escalation_count"
        ] > 0
    )

    if operational_work_open:
        factors.append(
            "unresolved_operational_work"
        )

    # -----------------------------------------------------
    # ESCALATION PRIORITY
    # -----------------------------------------------------

    escalation_priorities = {
        escalation["priority"]
        .strip()
        .lower()
        for escalation
        in operational["escalations"]
        if escalation.get("priority")
    }

    if (
        "high" in escalation_priorities
        or "critical" in escalation_priorities
    ):
        factors.append(
            "high_priority_escalation"
        )

    # -----------------------------------------------------
    # SEVERITY
    # -----------------------------------------------------

    if "critical" in escalation_priorities:
        severity = "critical"

    elif "high" in escalation_priorities:
        severity = "high"

    elif operational["escalation_count"] > 0:
        severity = "medium"

    elif operational["task_count"] > 0:
        severity = "low"

    else:
        severity = "unknown"

    return {
        "compensation_request_id":
            compensation_request_id,
        "severity":
            severity,
        "operational_evidence_available":
            operational_evidence_available,
        "operational_work_open":
            operational_work_open,
        "human_review_required":
            True,
        "factors":
            factors,
    }