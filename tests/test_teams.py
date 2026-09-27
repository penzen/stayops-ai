from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


def test_operations_technicians_returns_only_maintenance_workers(
    test_db,
):
    response = client.get(
        "/operations/technicians"
    )

    assert response.status_code == 200

    workers = response.json()

    assert len(workers) > 0

    assert all(
        worker["team_group"]
        == "technical_maintenance"
        for worker in workers
    )

    assert all(
        worker["team_id"]
        for worker in workers
    )