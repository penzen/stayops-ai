from backend.domain.playbooks import get_playbook


def test_get_heating_playbook():
    playbook = get_playbook("heating")

    assert playbook is not None
    assert playbook["category"] == "heating"

    assert playbook["required_checks"]
    assert playbook["operational_actions"]
    assert playbook["resolution_conditions"]


def test_playbook_lookup_is_case_insensitive():
    playbook = get_playbook("HEATING")

    assert playbook is not None
    assert playbook["category"] == "heating"


def test_unknown_playbook_returns_none():
    playbook = get_playbook(
        "does_not_exist"
    )

    assert playbook is None

def test_get_plumbing_playbook():
    playbook = get_playbook("plumbing")

    assert playbook is not None
    assert playbook["category"] == "plumbing"
    assert playbook["required_checks"]
    assert playbook["critical_conditions"]
    assert playbook["resolution_conditions"]


def test_get_refund_playbook():
    playbook = get_playbook("refund")

    assert playbook is not None
    assert playbook["category"] == "refund"
    assert playbook["approval_rules"]
    assert playbook["prohibited_guest_actions"]
    assert playbook["resolution_conditions"]