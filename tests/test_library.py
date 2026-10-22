"""Tests for the local track library."""

import pytest

from slothsounds.library import TrackLibrary


def _add(lib: TrackLibrary, vibe: str = "rainy piano") -> dict:
    return lib.add(
        kind="loop",
        vibe=vibe,
        prompt=f"{vibe}, ambient",
        source="heuristic",
        model="facebook/musicgen-small",
        seed=42,
        duration=30.0,
        path=lib.root / "loop.wav",
    )


def test_add_and_list(tmp_path):
    lib = TrackLibrary(tmp_path)
    entry = _add(lib)
    assert entry["id"]
    assert entry["kind"] == "loop"
    assert len(lib.all()) == 1
    assert lib.latest(10)[0]["id"] == entry["id"]


def test_persists_across_instances(tmp_path):
    lib = TrackLibrary(tmp_path)
    entry = _add(lib)
    lib2 = TrackLibrary(tmp_path)
    assert [e["id"] for e in lib2.all()] == [entry["id"]]


def test_path_stored_relative_to_root(tmp_path):
    lib = TrackLibrary(tmp_path)
    entry = _add(lib)
    assert entry["path"] == "loop.wav"


def test_latest_returns_newest_first(tmp_path):
    lib = TrackLibrary(tmp_path)
    first = _add(lib, "rain")
    second = _add(lib, "fireplace")
    assert [e["id"] for e in lib.latest(1)] == [second["id"]]
    assert first["id"] != second["id"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
