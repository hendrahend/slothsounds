"""Taste memory for Sloth Sounds, backed by Backboard's stateful API.

Backboard gives any AI app persistent memory across sessions. Sloth
Sounds uses it the lazy way: every generated loop is logged to a
long-lived assistant, and before a night set is built the assistant is
asked what it remembers about your taste — so the variations it suggests
match what you actually keep coming back to.

Works without a key (returns None everywhere); enable with:
    export SLOTHSOUNDS_BACKBOARD_KEY=...
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

BASE_URL = "https://app.backboard.io/api"
STATE_FILE = Path("out/memory_state.json")

SYSTEM_CONTENT = (
    "You are the taste memory for Sloth Sounds, a local ambient music "
    "generator. You remember which vibes and textures its owner keeps "
    "generating and liking. When asked, reply with ONE short variation "
    "hint (a few words, e.g. 'add distant thunder') or NONE if you have "
    "no useful memory yet."
)


class SlothMemory:
    def __init__(self, api_key: str | None = None, state_path: str | Path | None = None):
        self.api_key = api_key
        self.state_path = Path(state_path) if state_path else STATE_FILE
        self.assistant_id: str | None = None
        self.thread_id: str | None = None
        self._load_state()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _load_state(self) -> None:
        if self.state_path.exists():
            try:
                state = json.loads(self.state_path.read_text(encoding="utf-8"))
                self.assistant_id = state.get("assistant_id")
                self.thread_id = state.get("thread_id")
            except (json.JSONDecodeError, OSError):
                pass

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps({"assistant_id": self.assistant_id, "thread_id": self.thread_id}),
            encoding="utf-8",
        )

    def _send(self, content: str) -> dict | None:
        """Send one message on the persistent thread. Returns the API result."""
        if not self.enabled:
            return None
        payload: dict = {"content": content, "stream": False}
        if self.thread_id:
            payload["thread_id"] = self.thread_id
        if self.assistant_id:
            payload["assistant_id"] = self.assistant_id
        try:
            resp = requests.post(
                f"{BASE_URL}/threads/messages",
                json=payload,
                headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
        except (requests.RequestException, ValueError):
            return None

        # First exchange auto-creates the assistant + thread; persist them.
        changed = False
        if result.get("assistant_id") and result["assistant_id"] != self.assistant_id:
            self.assistant_id = result["assistant_id"]
            changed = True
        if result.get("thread_id") and result["thread_id"] != self.thread_id:
            self.thread_id = result["thread_id"]
            changed = True
        if changed:
            self._save_state()
        return result

    def remember_generation(
        self, vibe: str, prompt: str, seed: int | None, liked: bool | None = None
    ) -> str | None:
        """Log a generation so the assistant's memory accumulates taste."""
        verdict = ""
        if liked is True:
            verdict = " The owner liked this one."
        elif liked is False:
            verdict = " The owner skipped this one."
        content = (
            f"Generated an ambient loop for the vibe '{vibe}' "
            f"(seed {seed}). Music prompt used: {prompt}.{verdict}"
        )
        result = self._send(content)
        return result.get("content") if result else None

    def suggest_variation(self, vibe: str) -> str | None:
        """Ask the memory for a variation hint for the next segment."""
        result = self._send(
            f"Based on what you remember about this owner's taste, suggest ONE short "
            f"variation hint for a new segment with the vibe '{vibe}'. "
            f"Reply with the hint only, or NONE."
        )
        if not result:
            return None
        hint = (result.get("content") or "").strip()
        if not hint or hint.upper() == "NONE":
            return None
        return hint
