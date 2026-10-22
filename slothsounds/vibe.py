"""Vibe → music-prompt expansion.

Two paths, same output shape (a one-line MusicGen prompt):

1. A local open-weight LLM (Gemma 3 via Ollama) rewrites the lazy vibe
   into rich audio descriptors. This is the path that improves over time
   (and the one the Tinker fine-tune will replace with a specialist model).
2. A keyword heuristic that works with zero extra services, so the tool
   never hard-fails when Ollama is not running.
"""

from __future__ import annotations

import requests

# Lazy human vibe -> concrete audio descriptors. Keys are matched as
# substrings of the lowercased vibe, so "rainy" hits "rain".
KEYWORD_DESCRIPTORS: dict[str, list[str]] = {
    "rain": ["gentle rainfall", "distant rolling thunder"],
    "piano": ["soft felt-piano melody", "intimate close-miked piano"],
    "sleep": ["very slow tempo", "no percussion", "lullaby-like"],
    "bed": ["very slow tempo", "no percussion", "lullaby-like"],
    "night": ["nocturnal ambience", "quiet and dark"],
    "midnight": ["nocturnal ambience", "quiet and dark"],
    "morning": ["soft sunrise textures", "gentle awakening"],
    "dawn": ["soft sunrise textures", "gentle awakening"],
    "coffee": ["warm cafe ambiance", "soft chatter far in the distance"],
    "cafe": ["warm cafe ambiance", "soft chatter far in the distance"],
    "lofi": ["lofi hip hop drums", "vinyl crackle", "tape saturation"],
    "forest": ["birdsong", "wind through leaves"],
    "woods": ["birdsong", "wind through leaves"],
    "ocean": ["slow ocean waves", "deep drones"],
    "sea": ["slow ocean waves", "deep drones"],
    "wave": ["slow ocean waves", "deep drones"],
    "fire": ["crackling fireplace", "warm low drones"],
    "fireplace": ["crackling fireplace", "warm low drones"],
    "space": ["deep space drones", "slow evolving pads"],
    "cosmic": ["deep space drones", "slow evolving pads"],
    "synth": ["analog synth pads", "slow filter movement"],
    "guitar": ["fingerpicked acoustic guitar", "soft hall reverb"],
    "study": ["calm focus textures", "minimal percussion"],
    "focus": ["calm focus textures", "minimal percussion"],
    "work": ["calm focus textures", "minimal percussion"],
    "meditat": ["drone meditation", "singing bowl"],
    "calm": ["drone meditation", "singing bowl"],
    "relax": ["drone meditation", "singing bowl"],
    "jazz": ["soft jazz trio", "brushed drums", "upright bass"],
    "snow": ["muffled winter quiet", "soft high shimmer"],
    "winter": ["muffled winter quiet", "soft high shimmer"],
    "library": ["quiet room tone", "distant page turns"],
    "read": ["quiet room tone", "distant page turns"],
    "train": ["rhythmic train rumble", "soft rain on windows"],
    "travel": ["rhythmic train rumble", "soft rain on windows"],
    "sloth": ["unhurried and warm", "nothing to do"],
}

# Always appended so the model knows the target format.
BASE_SUFFIX = "ambient instrumental, seamless loop, high quality recording, no vocals"

OLLAMA_PROMPT_TEMPLATE = """Rewrite the following vibe into a single-line music generation prompt.

Rules:
- One line only, comma-separated audio descriptors.
- Under 40 words. No preamble, no explanation, no quotes.
- Keep the mood of the original vibe; add concrete instruments, texture and tempo hints.
- End with: seamless loop, no vocals

Vibe: {vibe}
Prompt:"""


def heuristic_expand(vibe: str) -> str:
    """Keyword-based vibe expansion. Always returns a usable prompt."""
    lowered = vibe.lower()
    descriptors: list[str] = []
    for keyword, hits in KEYWORD_DESCRIPTORS.items():
        if keyword in lowered:
            descriptors.extend(hits)
    # Dedupe, preserve order, cap so prompts stay tight.
    seen: set[str] = set()
    unique = [d for d in descriptors if not (d in seen or seen.add(d))][:6]
    parts = [vibe.strip(), *unique, BASE_SUFFIX]
    return ", ".join(p for p in parts if p)


def ollama_expand(
    vibe: str,
    model: str = "gemma3:4b",
    url: str = "http://localhost:11434",
    timeout: float = 30.0,
) -> str | None:
    """Ask a local Ollama model to expand the vibe. Returns None on any failure."""
    try:
        resp = requests.post(
            f"{url.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": OLLAMA_PROMPT_TEMPLATE.format(vibe=vibe),
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 120},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "").strip()
        # Models sometimes wrap output; keep the first non-empty line.
        text = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        return text or None
    except (requests.RequestException, ValueError, KeyError):
        return None


def expand_vibe(
    vibe: str,
    use_llm: bool = True,
    ollama_model: str = "gemma3:4b",
    ollama_url: str = "http://localhost:11434",
    timeout: float = 30.0,
) -> tuple[str, str]:
    """Expand a vibe into a music prompt.

    Returns (prompt, source) where source is "gemma" (local LLM) or
    "heuristic" (keyword fallback).
    """
    if use_llm:
        expanded = ollama_expand(vibe, model=ollama_model, url=ollama_url, timeout=timeout)
        if expanded:
            return expanded, "gemma"
    return heuristic_expand(vibe), "heuristic"
