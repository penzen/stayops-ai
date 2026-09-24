from backend.services.cases import (
    ensure_case,
    get_case,
)
from backend.services.demo import reset_demo_state


PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"


def test_reset_demo_state_removes_cases(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = case_result["case"]["case_id"]

    assert get_case(case_id) is not None

    reset_result = reset_demo_state(BOOKING_ID)

    assert reset_result["deleted"]["cases"] == 1
    assert get_case(case_id) is None