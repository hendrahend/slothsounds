"""Tests for vibe expansion."""

import pytest

from slothsounds.vibe import BASE_SUFFIX, expand_vibe, heuristic_expand, ollama_expand


def test_heuristic_maps_keywords():
    prompt = heuristic_expand("rainy sunday piano")
    assert "rainfall" in prompt
    assert "piano" in prompt
    assert BASE_SUFFIX in prompt


def test_heuristic_always_usable():
    prompt = heuristic_expand("zzz qqq unmatched vibe")
    assert prompt.strip()
    assert BASE_SUFFIX in prompt


def test_heuristic_dedupes_and_caps():
    # "sleep" and "bed" map to the same descriptors; they must not repeat.
    prompt = heuristic_expand("sleepy bedtime lofi rain piano forest ocean")
    assert prompt.count("no percussion") == 1


def test_expand_vibe_without_llm():
    prompt, source = expand_vibe("rainy sunday piano", use_llm=False)
    assert source == "heuristic"
    assert "rainfall" in prompt


def test_ollama_expand_returns_none_when_unreachable():
    # Port 1: connection refused immediately, no server needed.
    assert ollama_expand("rainy piano", url="http://127.0.0.1:1", timeout=1) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
