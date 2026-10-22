"""Tests for the Backboard taste-memory client.

All tests run with the client disabled (no API key) — they verify the
offline contract: no key, no network, no crashes, everything returns None.
"""

import pytest

from slothsounds.memory import SlothMemory


def test_disabled_without_key(tmp_path):
    mem = SlothMemory(api_key=None, state_path=tmp_path / "state.json")
    assert not mem.enabled
    assert mem.remember_generation("rainy piano", "rainy piano, ambient", 1) is None
    assert mem.suggest_variation("rainy piano") is None


def test_state_roundtrip(tmp_path):
    state = tmp_path / "state.json"
    mem = SlothMemory(api_key="test-key", state_path=state)
    mem.assistant_id = "asst_123"
    mem.thread_id = "thread_456"
    mem._save_state()

    mem2 = SlothMemory(api_key="test-key", state_path=state)
    assert mem2.assistant_id == "asst_123"
    assert mem2.thread_id == "thread_456"


def test_send_without_key_is_noop(tmp_path):
    mem = SlothMemory(api_key=None, state_path=tmp_path / "state.json")
    assert mem._send("hello") is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
