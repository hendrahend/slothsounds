"""Night mode: generate a full wind-down set while you sleep.

One vibe in, a multi-minute ambient set out — each segment gets a
variation hint so the piece evolves instead of repeating, and the whole
set crossfades seamlessly. Wake up to fresh music; that is the sloth
payoff.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from .audio import duration_seconds, normalize, write_wav
from .config import Settings
from .library import TrackLibrary
from .loops import join_segments, make_loop
from .vibe import expand_vibe

# Cycled across segments so the set has an arc: bloom, thin out,
# a distant melody, return home.
VARIATION_HINTS = [
    "slowly evolving pads",
    "sparser arrangement, more air",
    "a distant melody emerges",
    "textures deepen and slow further",
    "return to the opening warmth",
    "gentle resolution, fading textures",
]


def build_night_set(
    engine,
    vibe: str,
    minutes: int,
    settings: Settings,
    library: TrackLibrary,
    use_llm: bool = True,
    seed: int | None = None,
    progress=print,
) -> dict:
    """Generate a `minutes`-long set for `vibe`. Returns a result dict."""
    base_prompt, source = expand_vibe(
        vibe,
        use_llm=use_llm,
        ollama_model=settings.ollama_model,
        ollama_url=settings.ollama_url,
    )
    progress(f"vibe      : {vibe}")
    progress(f"prompt    : {base_prompt}  [{source}]")

    total_seconds = minutes * 60
    seg_len = min(settings.segment_seconds, total_seconds)
    n_segments = max(1, math.ceil(total_seconds / seg_len))
    fade = int(settings.sample_rate * settings.crossfade_seconds)

    out_dir = settings.ensure_output_dir()
    set_dir = out_dir / f"night-{vibe.strip().lower().replace(' ', '-')[:40]}-{_stamp()}"
    set_dir.mkdir(parents=True, exist_ok=True)

    segments: list[np.ndarray] = []
    segment_entries: list[dict] = []

    for i in range(n_segments):
        hint = VARIATION_HINTS[i % len(VARIATION_HINTS)]
        prompt = f"{base_prompt}, {hint}"
        seg_seed = None if seed is None else seed + i
        progress(f"segment {i + 1}/{n_segments}: {hint} (seed={seg_seed})")

        audio = engine.generate(
            prompt,
            duration=seg_len,
            seed=seg_seed,
            temperature=settings.temperature,
            top_k=settings.top_k,
            cfg_coef=settings.cfg_coef,
        )
        loop = make_loop(audio, settings.sample_rate, fade_seconds=settings.crossfade_seconds)
        loop = normalize(loop)

        seg_path = write_wav(set_dir / f"segment-{i + 1:02d}.wav", loop, settings.sample_rate)
        segments.append(loop)
        segment_entries.append(
            library.add(
                kind="segment",
                vibe=vibe,
                prompt=prompt,
                source=source,
                model=settings.model,
                seed=seg_seed,
                duration=duration_seconds(loop, settings.sample_rate),
                path=seg_path,
                set_dir=str(set_dir),
            )
        )

    full = normalize(join_segments(segments, settings.sample_rate, settings.crossfade_seconds))
    set_path = write_wav(set_dir / "full-set.wav", full, settings.sample_rate)

    run_sheet = _run_sheet(vibe, base_prompt, source, settings, segment_entries, set_path)
    (set_dir / "RUN-SHEET.md").write_text(run_sheet, encoding="utf-8")

    set_entry = library.add(
        kind="set",
        vibe=vibe,
        prompt=base_prompt,
        source=source,
        model=settings.model,
        seed=seed,
        duration=duration_seconds(full, settings.sample_rate),
        path=set_path,
        segments=len(segments),
    )
    progress(f"done      : {set_path} ({duration_seconds(full, settings.sample_rate) / 60:.1f} min)")
    return {
        "set_path": set_path,
        "set_dir": set_dir,
        "segments": segment_entries,
        "entry": set_entry,
    }


def _stamp() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _run_sheet(
    vibe: str,
    prompt: str,
    source: str,
    settings: Settings,
    segments: list[dict],
    set_path: Path,
) -> str:
    lines = [
        f"# Night set — {vibe}",
        "",
        f"- prompt: `{prompt}`",
        f"- prompt source: {source}",
        f"- model: {settings.model}",
        f"- segments: {len(segments)} x {settings.segment_seconds}s, "
        f"{settings.crossfade_seconds}s crossfade",
        f"- full set: `{Path(set_path).name}`",
        "",
        "| # | timecode | variation | seed |",
        "| --- | --- | --- | --- |",
    ]
    t = 0.0
    for i, seg in enumerate(segments, 1):
        mm, ss = divmod(int(t), 60)
        lines.append(f"| {i} | {mm:02d}:{ss:02d} | {seg['prompt'].split(', ', 1)[-1]} | {seg['seed']} |")
        t += seg["duration"]
    lines.append("")
    lines.append("Generated locally with Sloth Sounds. Nothing left this laptop.")
    return "\n".join(lines)
