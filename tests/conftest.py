import pytest

from backend.database.bootstrap import bootstrap_database


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Give each test its own isolated StayOps database.

    Service functions continue using the normal get_connection()
    path, but STAYOPS_DB_PATH redirects them to this temporary DB.
    """

    db_path = tmp_path / "stayops_test.db"

    bootstrap_database(
        db_path=db_path,
        force=False,
    )

    monkeypatch.setenv(
        "STAYOPS_DB_PATH",
        str(db_path),
    )

    return db_path


"""
pytest starts test
      ↓
creates temporary folder
      ↓
bootstrap_database()
      ↓
fresh StayOps database
      ↓
STAYOPS_DB_PATH = temporary database
      ↓
StayOps services operate on test DB
      ↓
test finishes
      ↓
temporary files disappear

"""