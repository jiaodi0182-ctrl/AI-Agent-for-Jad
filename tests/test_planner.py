import sys
sys.path.insert(0, ".")
import pytest
from unittest.mock import MagicMock, patch
from agent.planner import Planner


def make_mock_agent(chat_responses=None):
    agent = MagicMock()
    agent.model = "claude-sonnet-4-6"
    if chat_responses:
        agent.chat.side_effect = chat_responses
    else:
        agent.chat.return_value = "done"
    return agent


def make_mock_client(plan_json: str, summary: str = "Final answer"):
    client = MagicMock()
    plan_response = MagicMock()
    plan_response.content = [MagicMock(text=plan_json)]
    summary_response = MagicMock()
    summary_response.content = [MagicMock(text=summary)]
    client.messages.create.side_effect = [plan_response, summary_response]
    return client


def test_plan_and_execute_two_steps():
    agent = make_mock_agent(chat_responses=["result 1", "result 2"])
    agent.client = make_mock_client('["Step 1: search", "Step 2: summarize"]', "All done")
    planner = Planner(agent)

    result = planner.run("Do a complex task")
    assert result == "All done"
    assert agent.chat.call_count == 2


def test_on_step_callback():
    agent = make_mock_agent(chat_responses=["r1", "r2"])
    agent.client = make_mock_client('["step A", "step B"]', "summary")
    planner = Planner(agent)

    calls = []
    planner.run("task", on_step=lambda i, total, step, res: calls.append((i, total)))

    assert calls == [(1, 2), (2, 2)]


def test_fallback_on_invalid_json():
    agent = make_mock_agent()
    agent.client = make_mock_client("not valid json at all", "fallback result")
    planner = Planner(agent)

    # With invalid JSON, planner falls back to single-step (calls agent.chat directly)
    result = planner.run("simple task")
    assert agent.chat.call_count == 1


def test_single_step_task():
    agent = make_mock_agent()
    agent.client = make_mock_client('["Only one step"]', "done")
    planner = Planner(agent)

    result = planner.run("easy task")
    assert result == "done"
    assert agent.chat.call_count == 1
