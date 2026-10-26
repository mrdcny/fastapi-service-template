import uuid

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_readiness_ok_with_database(db_client: TestClient) -> None:
    response = db_client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["checks"] == {"database": "ok"}


def test_create_and_fetch_note(db_client: TestClient) -> None:
    created = db_client.post("/v1/notes", json={"title": "hello", "body": "world"})
    assert created.status_code == 201
    note = created.json()
    assert note["title"] == "hello"
    assert note["created_at"]

    fetched = db_client.get(f"/v1/notes/{note['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == note


def test_list_notes_newest_first(db_client: TestClient) -> None:
    for title in ("first", "second"):
        db_client.post("/v1/notes", json={"title": title})
    titles = [n["title"] for n in db_client.get("/v1/notes").json()]
    assert titles == ["second", "first"]


def test_missing_note_returns_404(db_client: TestClient) -> None:
    assert db_client.get(f"/v1/notes/{uuid.uuid4()}").status_code == 404


def test_validation_rejects_empty_title(db_client: TestClient) -> None:
    assert db_client.post("/v1/notes", json={"title": ""}).status_code == 422
