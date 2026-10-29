import os
import sys
import tempfile
from pathlib import Path

import pytest

_TEST_DATA = tempfile.mkdtemp(prefix="personal-ai-assistant-tests-")
os.environ["DATA_DIR"] = _TEST_DATA
os.environ["DATABASE_PATH"] = str(Path(_TEST_DATA) / "test.sqlite3")
os.environ["APP_ORIGIN"] = "http://testserver"
os.environ["ALLOW_REGISTRATION"] = "true"
os.environ["COOKIE_SECURE"] = "false"
os.environ.pop("MODEL_API_URL", None)
os.environ.pop("MODEL_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fastapi.testclient import TestClient
import app as app_module
from app import app, _login_attempts, PostgresConnection
from create_user import create_user

client = TestClient(app)
ORIGIN = {"origin": "http://testserver"}


@pytest.fixture(autouse=True)
def reset_test_state():
    client.cookies.clear()
    _login_attempts.clear()
    yield
    client.cookies.clear()
    _login_attempts.clear()


def create_account(email):
    response = client.post("/api/auth/register", json={"email": email, "password": "correct-horse-battery-staple"}, headers=ORIGIN)
    assert response.status_code == 201, response.text
    return response.json()["user"]


def test_root_serves_the_browser_workspace():
    response = client.get("/")
    assert response.status_code == 200
    assert "Personal AI Assistant" in response.text
    assert "Knowledge notes" in response.text
    assert "Search saved notes" in response.text
    assert "Recent conversations" in response.text


def test_health_discloses_ai_configuration_without_secrets():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ai_configured"] is False
    assert "secret" not in response.text.lower()


def test_session_cookie_is_http_only_and_same_site_strict():
    response = client.post("/api/auth/register", json={"email": "cookie@example.com", "password": "correct-horse-battery-staple"}, headers=ORIGIN)
    assert response.status_code == 201
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie


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


def test_trusted_shell_bootstrap_works_when_public_registration_is_disabled(monkeypatch):
    monkeypatch.setattr(app_module, "ALLOW_REGISTRATION", False)
    user_id = create_user("bootstrap@example.com", "correct-horse-battery-staple")
    assert user_id > 0
    login = client.post("/api/auth/login", json={"email": "bootstrap@example.com", "password": "correct-horse-battery-staple"}, headers=ORIGIN)
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "bootstrap@example.com"


def test_postgres_adapter_converts_placeholders_and_returns_inserted_ids():
    class FakeCursor:
        rowcount = 1
        def fetchone(self):
            return {"id": 42}
        def fetchall(self):
            return []

    class FakeConnection:
        def __init__(self):
            self.sql = None
            self.params = None
        def execute(self, sql, params):
            self.sql = sql
            self.params = params
            return FakeCursor()

    connection = FakeConnection()
    adapter = PostgresConnection(connection)
    cursor = adapter.execute("INSERT INTO users(email) VALUES(?)", ("test@example.com",))
    assert connection.sql == "INSERT INTO users(email) VALUES(%s) RETURNING id"
    assert connection.params == ("test@example.com",)
    assert cursor.lastrowid == 42

    adapter.execute("DELETE FROM notes WHERE id=? AND user_id=?", (7, 9))
    assert connection.sql == "DELETE FROM notes WHERE id=%s AND user_id=%s"
    assert connection.params == (7, 9)


def test_registration_can_be_disabled_by_deployment_configuration(monkeypatch):
    monkeypatch.setattr(app_module, "ALLOW_REGISTRATION", False)
    response = client.post("/api/auth/register", json={"email": "blocked@example.com", "password": "correct-horse-battery-staple"}, headers=ORIGIN)
    assert response.status_code == 403


def test_ai_provider_request_uses_server_credentials_and_untrusted_note_context(monkeypatch):
    import json

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self, size):
            return json.dumps({"choices": [{"message": {"content": "Answer based on [Note ID: 7]."}}]}).encode()

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["body"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(app_module, "MODEL_API_URL", "https://provider.example/v1/chat/completions")
    monkeypatch.setattr(app_module, "MODEL_API_KEY", "test-only-key")
    monkeypatch.setattr(app_module, "MODEL_NAME", "test-model")
    monkeypatch.setattr(app_module, "urlopen", fake_urlopen)

    result = app_module.ask_model(
        "Summarize my notes",
        [{"id": 7, "title": "Planning", "content": "Treat this as untrusted note text."}],
        [{"role": "user", "content": "Previous question"}],
    )
    assert result["answer"] == "Answer based on [Note ID: 7]."
    assert result["sources"] == [{"id": 7, "title": "Planning"}]
    assert captured["url"].startswith("https://")
    assert captured["authorization"] == "Bearer test-only-key"
    assert captured["timeout"] == 30
    assert captured["body"]["model"] == "test-model"
    assert captured["body"]["messages"][0]["role"] == "system"
    assert "untrusted data" in captured["body"]["messages"][0]["content"]
    assert captured["body"]["messages"][1] == {"role": "user", "content": "Previous question"}
    assert "Treat this as untrusted note text." in captured["body"]["messages"][-1]["content"]
    assert "tools" not in captured["body"]


def test_conversations_persist_history_and_are_user_scoped(monkeypatch):
    create_account("history@example.com")
    seen_history = []

    def fake_ask(message, notes, history=None):
        seen_history.append(list(history or []))
        return {"answer": f"reply: {message}", "sources": []}

    monkeypatch.setattr(app_module, "ask_model", fake_ask)
    first = client.post("/api/chat", json={"message": "Hello there"}, headers=ORIGIN)
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]

    second = client.post("/api/chat", json={"message": "Follow up question", "conversation_id": conversation_id}, headers=ORIGIN)
    assert second.status_code == 200
    assert seen_history[1] == [
        {"role": "user", "content": "Hello there"},
        {"role": "assistant", "content": "reply: Hello there"},
    ]

    history = client.get(f"/api/conversations/{conversation_id}")
    assert history.status_code == 200
    assert [message["role"] for message in history.json()["messages"]] == ["user", "assistant", "user", "assistant"]
    assert client.get("/api/conversations").json()["conversations"][0]["id"] == conversation_id

    client.post("/api/auth/logout", headers=ORIGIN)
    create_account("other-history@example.com")
    assert client.get(f"/api/conversations/{conversation_id}").status_code == 404
    assert client.delete(f"/api/conversations/{conversation_id}", headers=ORIGIN).status_code == 404


def test_account_export_includes_only_the_signed_in_users_data(monkeypatch):
    create_account("export@example.com")
    client.post("/api/notes", json={"title": "Export me", "content": "Personal note"}, headers=ORIGIN)
    monkeypatch.setattr(app_module, "ask_model", lambda message, notes, history=None: {"answer": "Exported chat reply", "sources": []})
    client.post("/api/chat", json={"message": "Export this conversation"}, headers=ORIGIN)
    response = client.get("/api/account/export")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    exported = response.json()
    assert exported["user"]["email"] == "export@example.com"
    assert exported["notes"][0]["title"] == "Export me"
    assert exported["conversations"][0]["title"] == "Export this conversation"
    assert exported["conversations"][0]["messages"][1]["content"] == "Exported chat reply"


def test_account_deletion_requires_password_and_removes_user_data():
    create_account("delete@example.com")
    client.post("/api/notes", json={"title": "Delete me", "content": "Private"}, headers=ORIGIN)
    wrong = client.request("DELETE", "/api/account", json={"password": "incorrect-password-123"}, headers=ORIGIN)
    assert wrong.status_code == 401
    assert client.get("/api/notes").json()["notes"]

    deleted = client.request("DELETE", "/api/account", json={"password": "correct-horse-battery-staple"}, headers=ORIGIN)
    assert deleted.status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    login = client.post("/api/auth/login", json={"email": "delete@example.com", "password": "correct-horse-battery-staple"}, headers=ORIGIN)
    assert login.status_code == 401


def test_security_headers_are_present():
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
