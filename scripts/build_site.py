"""Build the static demo site from the local library.

Copies generated loops and the latest night set into site/, writes
site/tracks.json, and regenerates the player page. Run after generating:

    python scripts/build_site.py

Then commit and push — Render auto-deploys the site/ directory.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"


def build(library_dir: Path = ROOT / "out") -> None:
    from slothsounds.library import TrackLibrary

    library = TrackLibrary(library_dir)
    entries = [e for e in library.all() if e["kind"] in ("loop", "set")]

    audio_dir = SITE / "audio"
    if audio_dir.exists():
        shutil.rmtree(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)

    tracks = []
    for e in entries:
        src = library_dir / e["path"]
        if not src.exists():
            continue
        dst = audio_dir / src.name
        shutil.copy2(src, dst)
        tracks.append({
            "id": e["id"],
            "kind": e["kind"],
            "vibe": e["vibe"],
            "prompt": e["prompt"],
            "duration": e["duration"],
            "file": f"audio/{src.name}",
            "created_at": e["created_at"],
        })

    (SITE / "tracks.json").write_text(
        json.dumps({"tracks": tracks}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"site built: {len(tracks)} tracks -> {SITE}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the static demo site")
    parser.add_argument("--dir", default="out", help="library directory (default: out/)")
    args = parser.parse_args()
    build(Path(args.dir))
