import sys
sys.path.insert(0, ".")
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api.server import app
from api import auth

client = TestClient(app)

HEADERS = {"X-API-Key": "test-key-123"}


@pytest.fixture(autouse=True)
def patch_auth(monkeypatch):
    monkeypatch.setattr(auth, "_load_keys", lambda: {"test-key-123": "testuser"})
    auth._windows.clear()


@pytest.fixture
def mock_agent():
    with patch("api.routes.chat._make_agent") as factory:
        agent = MagicMock()
        agent.chat.return_value = "test response"
        agent.stream.return_value = iter(["hello ", "world"])
        factory.return_value = agent
        yield agent


def test_chat_endpoint(mock_agent):
    r = client.post("/chat", json={"message": "test"}, headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["reply"] == "test response"
    assert "duration_ms" in data


def test_chat_with_planner(mock_agent):
    with patch("api.routes.chat.Planner") as MockPlanner:
        MockPlanner.return_value.run.return_value = "planner result"
        r = client.post("/chat", json={"message": "complex task", "use_planner": True}, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["reply"] == "planner result"


def test_stream_endpoint(mock_agent):
    r = client.post("/chat/stream", json={"message": "hi"}, headers=HEADERS)
    assert r.status_code == 200
    assert "hello" in r.text


def test_memory_stats():
    with patch("api.routes.memory._ltm") as mock_ltm:
        mock_ltm.count = 42
        r = client.get("/memory/stats", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["total_memories"] == 42


def test_memory_search():
    with patch("api.routes.memory._ltm") as mock_ltm:
        mock_ltm.count = 5
        mock_ltm.retrieve.return_value = [
            {"role": "user", "content": "hello", "timestamp": 1234567890.0}
        ]
        r = client.post("/memory/search", json={"query": "hello", "n_results": 3}, headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["content"] == "hello"


def test_memory_clear():
    with patch("api.routes.memory._ltm") as mock_ltm:
        r = client.delete("/memory/clear", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "cleared"
    mock_ltm.clear.assert_called_once()


def test_empty_message_rejected():
    r = client.post("/chat", json={"message": ""}, headers=HEADERS)
    assert r.status_code == 422
