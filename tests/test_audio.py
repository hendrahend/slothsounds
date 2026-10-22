"""Tests for WAV I/O, crossfades and seamless loops."""

import numpy as np
import pytest

from slothsounds.audio import (
    crossfade_concat,
    duration_seconds,
    make_seamless,
    normalize,
    read_wav,
    write_wav,
)
from slothsounds.loops import join_segments, make_loop


def _sine(sr: int, seconds: float, freq: float = 220.0) -> np.ndarray:
    t = np.arange(int(sr * seconds)) / sr
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_wav_roundtrip(tmp_path):
    sr = 32000
    data = _sine(sr, 0.5)
    path = write_wav(tmp_path / "t.wav", data, sr)
    loaded, loaded_sr = read_wav(path)
    assert loaded_sr == sr
    assert len(loaded) == len(data)
    assert np.allclose(loaded, data, atol=1e-3)


def test_write_wav_clips(tmp_path):
    data = np.array([2.0, -2.0, 0.0], dtype=np.float32)
    path = write_wav(tmp_path / "clip.wav", data, 8000)
    loaded, _ = read_wav(path)
    assert np.max(np.abs(loaded)) <= 1.0


def test_crossfade_concat_length():
    sr = 1000
    a, b = _sine(sr, 1.0, 220), _sine(sr, 1.0, 330)
    fade = int(sr * 0.5)
    out = crossfade_concat(a, b, fade)
    assert len(out) == len(a) + len(b) - fade
    assert np.all(np.isfinite(out))


def test_crossfade_zero_is_plain_concat():
    a = np.ones(10, dtype=np.float32)
    b = np.ones(5, dtype=np.float32)
    assert len(crossfade_concat(a, b, 0)) == 15


def test_make_seamless_preserves_length():
    sr = 32000
    data = _sine(sr, 2.0)
    out = make_seamless(data, sr, fade_seconds=1.0)
    assert len(out) == len(data)
    assert np.all(np.isfinite(out))


def test_make_seamless_short_input_untouched():
    data = _sine(1000, 0.1)
    out = make_seamless(data, 1000, fade_seconds=1.0)
    assert len(out) == len(data)


def test_normalize_hits_target_peak():
    data = _sine(1000, 0.5) * 0.1
    out = normalize(data, target_peak=0.89)
    assert np.isclose(np.max(np.abs(out)), 0.89, atol=1e-6)


def test_normalize_silence_stays_silent():
    data = np.zeros(100, dtype=np.float32)
    assert np.all(normalize(data) == 0.0)


def test_make_loop_and_join():
    sr = 8000
    segs = [_sine(sr, 1.0, f) for f in (220, 277, 330)]
    loops = [make_loop(s, sr, fade_seconds=0.25) for s in segs]
    joined = join_segments(loops, sr, crossfade_seconds=0.25)
    expected = sum(len(s) for s in loops) - 2 * int(sr * 0.25)
    assert len(joined) == expected
    assert duration_seconds(joined, sr) == pytest.approx(len(joined) / sr)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
