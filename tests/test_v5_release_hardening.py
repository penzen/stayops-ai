from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.demo_sessions import create_demo_session


client = TestClient(app)


def _headers(session):
    return {
        "X-StayOps-Demo-Token":
            session["session_token"],
    }


def test_public_catalog_requires_demo_session(
    test_db,
    monkeypatch,
):
    monkeypatch.delenv(
        "STAYOPS_ALLOW_LEGACY_DEMO",
        raising=False,
    )

    response = client.get(
        "/demo/properties"
    )

    assert response.status_code == 401


def test_public_catalog_accepts_valid_demo_session(
    test_db,
):
    session = create_demo_session()

    response = client.get(
        "/demo/properties",
        headers=_headers(session),
    )

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_operations_technicians_require_session(
    test_db,
    monkeypatch,
):
    monkeypatch.delenv(
        "STAYOPS_ALLOW_LEGACY_DEMO",
        raising=False,
    )

    response = client.get(
        "/operations/technicians"
    )

    assert response.status_code == 401


def test_property_reads_require_session(
    test_db,
    monkeypatch,
):
    monkeypatch.delenv(
        "STAYOPS_ALLOW_LEGACY_DEMO",
        raising=False,
    )

    property_response = client.get(
        "/properties/prop_15"
    )
    access_response = client.get(
        "/properties/prop_15/access"
    )

    assert property_response.status_code == 401
    assert access_response.status_code == 401


def test_property_reads_accept_valid_session(
    test_db,
):
    session = create_demo_session()

    property_response = client.get(
        "/properties/prop_15",
        headers=_headers(session),
    )
    access_response = client.get(
        "/properties/prop_15/access",
        headers=_headers(session),
    )

    assert property_response.status_code == 200

    # The seeded property may or may not have an access
    # system, but authentication must no longer be the
    # reason for rejection.
    assert access_response.status_code in {200, 404}
