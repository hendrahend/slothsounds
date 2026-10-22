"""Local library of everything Sloth Sounds has generated.

A single JSON file (out/library.json) tracks each loop and night set:
the vibe, the expanded prompt, which model/seed made it, and where the
audio lives. This is also the store the Backboard memory integration
will sync from later.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class TrackLibrary:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "library.json"
        self._entries: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._entries = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._entries = []

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self._entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(
        self,
        kind: str,
        vibe: str,
        prompt: str,
        source: str,
        model: str,
        seed: int | None,
        duration: float,
        path: str | Path,
        **extra,
    ) -> dict:
        entry = {
            "id": _new_id(),
            "kind": kind,  # "loop" | "set" | "segment"
            "vibe": vibe,
            "prompt": prompt,
            "source": source,  # "gemma" | "heuristic"
            "model": model,
            "seed": seed,
            "duration": round(float(duration), 2),
            "path": str(Path(path).relative_to(self.root))
            if str(path).startswith(str(self.root))
            else str(path),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **extra,
        }
        self._entries.append(entry)
        self.save()
        return entry

    def all(self) -> list[dict]:
        return list(self._entries)

    def latest(self, n: int = 10) -> list[dict]:
        return self._entries[-n:][::-1]
