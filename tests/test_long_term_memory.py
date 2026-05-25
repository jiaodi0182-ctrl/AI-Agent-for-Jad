import sys, tempfile
sys.path.insert(0, ".")
import pytest
from agent.long_term_memory import LongTermMemory


@pytest.fixture
def ltm(tmp_path):
    return LongTermMemory(db_path=str(tmp_path / "test_db"))


def test_save_and_count(ltm):
    ltm.save("user", "I love Python programming")
    ltm.save("assistant", "Python is a great language")
    assert ltm.count == 2


def test_retrieve_relevant(ltm):
    ltm.save("user", "What is the capital of France?")
    ltm.save("assistant", "The capital of France is Paris.")
    ltm.save("user", "Tell me about machine learning")
    ltm.save("assistant", "Machine learning is a subset of AI.")

    results = ltm.retrieve("France capital city", n_results=2)
    assert len(results) == 2
    assert any("France" in r["content"] or "Paris" in r["content"] for r in results)


def test_retrieve_empty(ltm):
    results = ltm.retrieve("anything", n_results=5)
    assert results == []


def test_format_for_prompt_empty(ltm):
    result = ltm.format_for_prompt("test query")
    assert result == ""


def test_format_for_prompt_with_data(ltm):
    ltm.save("user", "My name is Jad and I like coffee")
    result = ltm.format_for_prompt("who am I")
    assert "历史记忆" in result
    assert "Jad" in result


def test_clear(ltm):
    ltm.save("user", "some message")
    ltm.clear()
    assert ltm.count == 0
