"""Runtime settings for Sloth Sounds.

Defaults are tuned for a laptop GPU (or CPU) running MusicGen small.
Every value can be overridden with a SLOTHSOUNDS_* environment variable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(key: str, default: str) -> str:
    return os.environ.get(f"SLOTHSOUNDS_{key}", default)


@dataclass
class Settings:
    # Where generated audio and the library metadata live.
    output_dir: Path = field(default_factory=lambda: Path(_env("OUTPUT_DIR", "out")))

    # Open-weight music model (audiocraft / MusicGen family).
    model: str = field(default_factory=lambda: _env("MODEL", "facebook/musicgen-small"))

    # Local LLM used to expand lazy vibes into music prompts (optional).
    ollama_url: str = field(default_factory=lambda: _env("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _env("OLLAMA_MODEL", "gemma3:4b"))

    # Night mode: length of one generated segment and the crossfade between them.
    segment_seconds: int = field(default_factory=lambda: int(_env("SEGMENT_SECONDS", "30")))
    crossfade_seconds: float = field(default_factory=lambda: float(_env("CROSSFADE_SECONDS", "2.0")))

    # MusicGen native sample rate.
    sample_rate: int = 32000

    # Generation params (ambient-leaning defaults).
    temperature: float = 0.9
    top_k: int = 250
    cfg_coef: float = 3.0

    def ensure_output_dir(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir
