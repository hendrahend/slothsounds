"""Build the vibe-translator training dataset.

Each example teaches a small open-weight model to turn a lazy human vibe
("rainy sunday piano") into a MusicGen-optimized prompt (comma-separated
audio descriptors). The teacher is Gemma 3 via Ollama when available,
falling back to Sloth Sounds' keyword expander — so the dataset can be
built offline.

Output: data/vibe_dataset.jsonl (chat format, ready for Tinker SFT).
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from slothsounds.vibe import heuristic_expand, ollama_expand

SYSTEM_PROMPT = (
    "You are the vibe translator for Sloth Sounds, a local ambient music "
    "generator. You turn lazy human vibes into single-line music generation "
    "prompts: comma-separated audio descriptors, under 40 words, concrete "
    "instruments and textures, ending with 'seamless loop, no vocals'. "
    "No preamble, no explanation."
)

# Lazy vibes across moods, seasons, places and chores — the kind of
# things people actually type when they cannot be bothered to curate.
VIBES = [
    # weather & seasons
    "rainy sunday piano", "rain on the window while i study",
    "gentle thunderstorm for sleeping", "snow falling outside",
    "first snow of winter", "warm rain on leaves", "foggy morning",
    "windy autumn afternoon", "spring birds at dawn", "hot summer night",
    "cloudy day by the fire", "ice melting on the roof",
    # places
    "empty library at night", "small cafe on a rainy day",
    "train through the countryside", "night bus home",
    "airport at 3am", "bookstore before opening", "lighthouse in a storm",
    "mountain cabin", "desert night sky", "ocean from a hammock",
    "rooftop at midnight", "old church organ",
    # sleep & wind-down
    "slow ambient for sleep", "bedtime lullaby", "drone for deep sleep",
    "something to help me unwind", "music for turning off my brain",
    "2am cannot sleep", "sunday morning dozing",
    # focus & work
    "lofi for coding", "quiet focus music", "writing all-nighter fuel",
    "spreadsheet sunday", "inbox zero background", "studying for exams",
    "creative flow", "cleaning the apartment",
    # textures & instruments
    "felt piano and tape hiss", "analog synth pads", "nylon guitar",
    "cello in a big room", "harp and reverb", "marimba loop",
    "music box slowing down", "singing bowls",
    # feelings
    "music for a slow heart", "after a long day",
    "missing someone quietly", "hopeful but tired", "contented silence",
    "rainy day nostalgia", "last day of summer",
    # the sloth corner
    "sloth energy", "nothing to do", "moving at sloth pace",
    "hanging around all day", "maximum laziness",
    # scenes
    "fireplace while it snows", "cooking dinner slowly",
    "rainy bus stop", "aquarium at night", "greenhouse in the rain",
    "laundromat at midnight", "park bench after rain", "lakeside at dusk",
    "campfire and crickets", "sailing at night", "observatory",
    "seed vault", "typewriter shop", "clock repair shop",
    # longer phrasings
    "i want to read but it is raining and i keep getting distracted",
    "something warm for a gray tuesday", "music that feels like a blanket",
    "sounds like walking home at 2am", "background for a slow sunday",
    "make it feel like a hug", "i am too tired to pick a playlist",
    "just play something soft", "surprise me but keep it calm",
    "the audio equivalent of decaf",
]


def teacher_expand(vibe: str, use_ollama: bool = True) -> tuple[str, str]:
    """Return (prompt, teacher) for one vibe."""
    if use_ollama:
        expanded = ollama_expand(vibe, timeout=20)
        if expanded:
            return expanded, "gemma3"
    return heuristic_expand(vibe), "heuristic"


def build_dataset(out_path: str | Path, use_ollama: bool = True, seed: int = 0) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    vibes = list(VIBES)
    random.Random(seed).shuffle(vibes)

    rows = []
    teachers: dict[str, int] = {}
    for i, vibe in enumerate(vibes, 1):
        prompt, teacher = teacher_expand(vibe, use_ollama=use_ollama)
        teachers[teacher] = teachers.get(teacher, 0) + 1
        rows.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": vibe},
                {"role": "assistant", "content": prompt},
            ]
        })
        if i % 20 == 0:
            print(f"  {i}/{len(vibes)} examples built")

    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"wrote {len(rows)} examples to {out_path}")
    print(f"teachers: {teachers}")
    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the vibe-translator dataset")
    parser.add_argument("--out", default="data/vibe_dataset.jsonl")
    parser.add_argument("--no-ollama", action="store_true",
                        help="use the keyword expander only (fully offline)")
    args = parser.parse_args()
    build_dataset(args.out, use_ollama=not args.no_ollama)