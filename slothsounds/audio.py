"""WAV I/O and DSP helpers — stdlib `wave` + numpy only.

Kept dependency-light on purpose: loops, seams and the whole test suite
run without torch installed.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


def read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Read a mono or stereo WAV as float32 in [-1, 1]. Returns (data, sample_rate)."""
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        raw = w.readframes(w.getnframes())

    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    elif sampwidth == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        raise ValueError(f"unsupported sample width: {sampwidth} bytes")

    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)
    return data, sr


def write_wav(path: str | Path, data: np.ndarray, sr: int) -> Path:
    """Write float32 data in [-1, 1] as a 16-bit mono WAV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(data, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path


def crossfade_concat(a: np.ndarray, b: np.ndarray, fade_samples: int) -> np.ndarray:
    """Concatenate a and b with an equal-power crossfade.

    Result length is len(a) + len(b) - fade_samples.
    """
    if fade_samples <= 0:
        return np.concatenate([a, b])
    fade = min(fade_samples, len(a), len(b))
    t = np.linspace(0.0, np.pi / 2.0, fade, endpoint=False)
    seam = a[-fade:] * np.cos(t) + b[:fade] * np.sin(t)
    return np.concatenate([a[:-fade], seam, b[fade:]])


def make_seamless(data: np.ndarray, sr: int, fade_seconds: float = 1.5) -> np.ndarray:
    """Crossfade the tail of a clip into its head so it loops without a click.

    Length is preserved: the loop point lands inside the crossfaded region.
    """
    fade = int(sr * fade_seconds)
    if len(data) <= 2 * fade:
        return data.copy()
    head, tail = data[:fade], data[-fade:]
    t = np.linspace(0.0, np.pi / 2.0, fade, endpoint=False)
    seam = tail * np.cos(t) + head * np.sin(t)
    return np.concatenate([data[:-fade], seam])


def normalize(data: np.ndarray, target_peak: float = 0.89) -> np.ndarray:
    """Scale so the loudest sample sits at target_peak (leaves headroom for MP3)."""
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    if peak == 0.0:
        return data
    return data * (target_peak / peak)


def duration_seconds(data: np.ndarray, sr: int) -> float:
    return len(data) / float(sr)
