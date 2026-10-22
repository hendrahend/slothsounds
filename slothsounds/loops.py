"""Seamless loop construction."""

from __future__ import annotations

import numpy as np

from .audio import crossfade_concat, make_seamless


def make_loop(data: np.ndarray, sr: int, fade_seconds: float = 1.5) -> np.ndarray:
    """Turn a generated clip into a click-free loop."""
    return make_seamless(data, sr, fade_seconds=fade_seconds)


def join_segments(
    segments: list[np.ndarray],
    sr: int,
    crossfade_seconds: float = 2.0,
) -> np.ndarray:
    """Join generated segments into one continuous piece with crossfades."""
    if not segments:
        raise ValueError("no segments to join")
    fade = int(sr * crossfade_seconds)
    out = segments[0]
    for seg in segments[1:]:
        out = crossfade_concat(out, seg, fade)
    return out
