import os
import sys
import tempfile
from pathlib import Path

_TEST_DATA = tempfile.mkdtemp(prefix="personal-ai-assistant-tests-")
os.environ["DATA_DIR"] = _TEST_DATA
os.environ["DATABASE_PATH"] = str(Path(_TEST_DATA) / "test.sqlite3")
os.environ["APP_ORIGIN"] = "http://testserver"
os.environ["ALLOW_REGISTRATION"] = "true"
os.environ["COOKIE_SECURE"] = "false"
os.environ.pop("MODEL_API_URL", None)
os.environ.pop("MODEL_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import app, _login_attempts

client = TestClient(app)
ORIGIN = {"origin": "http://testserver"}


def create_account(email):
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse-battery-staple"}, headers=ORIGIN)
    assert response.status_code == 201, response.text
    return response.json()["user"]


def test_root_serves_the_browser_workspace():
    response = client.get("/")
    assert response.status_code == 200
    assert "Personal AI Assistant" in response.text
    assert "Knowledge notes" in response.text


def test_health_discloses_ai_configuration_without_secrets():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ai_configured"] is False
    assert "secret" not in response.text.lower()


def test_notes_require_authentication():
    response = client.get("/api/notes")
    assert response.status_code == 401


def test_user_can_create_list_update_and_delete_own_notes():
    create_account("alice@example.com")
    created = client.post("/api/notes", json={"title": "Project", "content": "Private notes"}, headers=ORIGIN)
    assert created.status_code == 201
    note = created.json()["note"]
    assert note["title"] == "Project"
    assert client.get("/api/notes").json()["notes"][0]["id"] == note["id"]

    updated = client.put(f"/api/notes/{note['id']}", json={"title": "Updated", "content": "Revised"}, headers=ORIGIN)
    assert updated.status_code == 200
    assert updated.json()["note"]["title"] == "Updated"

    deleted = client.delete(f"/api/notes/{note['id']}", headers=ORIGIN)
    assert deleted.status_code == 204
    assert client.get("/api/notes").json()["notes"] == []


def test_notes_are_isolated_between_accounts():
    create_account("bob@example.com")
    bob_note = client.post("/api/notes", json={"title": "Bob", "content": "Bob's secret"}, headers=ORIGIN).json()["note"]
    client.post("/api/auth/logout", headers=ORIGIN)

    create_account("carol@example.com")
    assert client.get("/api/notes").json()["notes"] == []
    assert client.get(f"/api/notes/{bob_note['id']}").status_code == 404
    assert client.put(f"/api/notes/{bob_note['id']}", json={"title": "Intrusion", "content": "x"}, headers=ORIGIN).status_code == 404
    assert client.delete(f"/api/notes/{bob_note['id']}", headers=ORIGIN).status_code == 404


def test_logout_invalidates_session():
    create_account("dave@example.com")
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout", headers=ORIGIN).status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_browser_writes_reject_wrong_origin():
    create_account("eve@example.com")
    response = client.post("/api/notes", json={"title": "Nope", "content": "x"}, headers={"origin": "https://attacker.invalid"})
    assert response.status_code == 403


def test_password_policy_is_enforced():
    response = client.post("/api/auth/register", json={"email": "short@example.com", "password": "tiny"}, headers=ORIGIN)
    assert response.status_code == 422


def test_chat_fails_safely_when_provider_is_not_configured():
    create_account("chat@example.com")
    response = client.post("/api/chat", json={"message": "What is in my notes?"}, headers=ORIGIN)
    assert response.status_code == 503
    assert "MODEL_API_URL" in response.json()["detail"]


def test_security_headers_are_present():
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
