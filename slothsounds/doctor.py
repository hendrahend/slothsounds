"""Environment doctor: what is installed, what is missing, what to do.

Core (numpy) is required for the CLI and tests. torch/audiocraft are
needed for actual generation. ffmpeg (MP3 export) and Ollama (LLM vibe
expansion) are optional upgrades.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass

import numpy as np
import requests

from .config import Settings


@dataclass
class Check:
    ok: bool
    label: str
    detail: str
    required: bool = False


def run_checks(settings: Settings | None = None) -> list[Check]:
    settings = settings or Settings()
    checks: list[Check] = []

    checks.append(Check(sys.version_info >= (3, 10), "Python >= 3.10",
                        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                        required=True))
    checks.append(Check(True, "numpy", np.__version__, required=True))

    # torch
    try:
        import torch

        cuda = torch.cuda.is_available()
        gpu = torch.cuda.get_device_name(0) if cuda else "cpu only"
        checks.append(Check(True, "torch", f"{torch.__version__} ({gpu})", required=True))
    except ImportError:
        checks.append(Check(False, "torch", "not installed — pip install torch "
                            "--index-url https://download.pytorch.org/whl/cu121", required=True))

    # audiocraft
    try:
        import audiocraft

        checks.append(Check(True, "audiocraft", audiocraft.__version__, required=True))
    except ImportError:
        checks.append(Check(False, "audiocraft",
                            "not installed — pip install audiocraft --no-deps "
                            "(Windows: see README)", required=True))

    # ffmpeg (optional, MP3 export)
    ffmpeg = shutil.which("ffmpeg")
    checks.append(Check(bool(ffmpeg), "ffmpeg", ffmpeg or "not found (optional, MP3 export only)"))

    # Ollama (optional, LLM vibe expansion)
    try:
        resp = requests.get(f"{settings.ollama_url.rstrip('/')}/api/tags", timeout=3)
        models = [m["name"] for m in resp.json().get("models", [])]
        has_gemma = any(settings.ollama_model in m for m in models)
        checks.append(Check(has_gemma, "ollama",
                            f"reachable, models: {', '.join(models) or 'none'}"
                            + ("" if has_gemma else f" — run: ollama pull {settings.ollama_model}")))
    except requests.RequestException:
        checks.append(Check(False, "ollama",
                            f"not reachable at {settings.ollama_url} (optional, "
                            "heuristic vibe expansion will be used)"))

    return checks


def print_report(checks: list[Check]) -> bool:
    """Print the report. Returns True if all required checks pass."""
    width = max(len(c.label) for c in checks)
    core_ok = True
    for c in checks:
        mark = "OK  " if c.ok else ("MISS" if c.required else "--  ")
        print(f"[{mark}] {c.label.ljust(width)}  {c.detail}")
        if c.required and not c.ok:
            core_ok = False
    print()
    if core_ok:
        print("Ready to generate. Try:  slothsounds gen \"rainy sunday piano\"")
    else:
        print("Missing required pieces — install them, then re-run:  slothsounds doctor")
    return core_ok
