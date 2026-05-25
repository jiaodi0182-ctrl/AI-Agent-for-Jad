import sys
sys.path.insert(0, ".")
import pytest
from agent.memory import Memory


def test_add_and_get():
    m = Memory()
    m.add("user", "hello")
    m.add("assistant", "hi")
    assert len(m.get()) == 2
    assert m.get()[0] == {"role": "user", "content": "hello"}


def test_max_turns_trimming():
    m = Memory(max_turns=2)
    for i in range(5):
        m.add("user", f"msg {i}")
        m.add("assistant", f"reply {i}")
    # max_turns=2 → keeps last 4 messages
    assert len(m.get()) == 4


def test_clear():
    m = Memory()
    m.add("user", "test")
    m.clear()
    assert len(m) == 0
