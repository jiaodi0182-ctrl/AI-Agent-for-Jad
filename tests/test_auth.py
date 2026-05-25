import sys
sys.path.insert(0, ".")
import time
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.server import app
from api import auth

client = TestClient(app)


@pytest.fixture(autouse=True)
def use_test_keys(monkeypatch):
    monkeypatch.setattr(auth, "_load_keys", lambda: {"test-key-123": "testuser"})
    # Reset rate limit windows between tests
    auth._windows.clear()


def test_health_no_auth():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_missing_key_returns_401():
    r = client.post("/chat", json={"message": "hello"})
    assert r.status_code == 401


def test_invalid_key_returns_401():
    r = client.post("/chat", json={"message": "hello"}, headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_valid_key_passes_auth():
    with patch("api.routes.chat._make_agent") as mock_agent_factory:
        mock_agent = mock_agent_factory.return_value
        mock_agent.chat.return_value = "hello back"
        r = client.post("/chat", json={"message": "hello"}, headers={"X-API-Key": "test-key-123"})
    assert r.status_code == 200
    assert r.json()["reply"] == "hello back"


def test_rate_limit_enforced(monkeypatch):
    monkeypatch.setattr(auth, "_RATE_LIMIT", 3)
    with patch("api.routes.chat._make_agent") as mock_agent_factory:
        mock_agent = mock_agent_factory.return_value
        mock_agent.chat.return_value = "ok"
        for _ in range(3):
            r = client.post("/chat", json={"message": "hi"}, headers={"X-API-Key": "test-key-123"})
            assert r.status_code == 200
        # 4th request should be rate-limited
        r = client.post("/chat", json={"message": "hi"}, headers={"X-API-Key": "test-key-123"})
        assert r.status_code == 429
