import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import smoke_test


def test_smoke_url_requires_https_for_remote_hosts():
    assert smoke_test.validate_base_url("https://assistant.example.com/") == "https://assistant.example.com"
    assert smoke_test.validate_base_url("http://127.0.0.1:8000/") == "http://127.0.0.1:8000"
    with pytest.raises(ValueError):
        smoke_test.validate_base_url("http://assistant.example.com")
    with pytest.raises(ValueError):
        smoke_test.validate_base_url("https://user:password@assistant.example.com")


def test_smoke_checks_health_csp_and_assets(monkeypatch):
    health = {
        "status": "ok",
        "database": "postgresql",
        "rate_limit_store": "redis",
        "ai_configured": True,
    }

    def fake_fetch(base_url, path):
        if path == "/health":
            return 200, {}, json.dumps(health).encode()
        if path == "/":
            return 200, {"Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'"}, b"<title>Personal AI Assistant</title>"
        if path in {"/assets/app.js", "/assets/styles.css"}:
            return 200, {}, b"asset"
        raise AssertionError(path)

    monkeypatch.setattr(smoke_test, "fetch", fake_fetch)
    result = smoke_test.run_checks("https://assistant.example.com", require_ai=True, require_postgres=True, require_redis=True)
    assert result == health


def test_smoke_checks_enforce_required_components(monkeypatch):
    health = {"status": "ok", "database": "sqlite", "rate_limit_store": "process-local", "ai_configured": False}

    def fake_fetch(base_url, path):
        if path == "/health":
            return 200, {}, json.dumps(health).encode()
        raise AssertionError("Should stop after failed health requirements")

    monkeypatch.setattr(smoke_test, "fetch", fake_fetch)
    with pytest.raises(RuntimeError, match="AI provider is not configured"):
        smoke_test.run_checks("https://assistant.example.com", require_ai=True)
