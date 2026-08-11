"""Durable human-memory store for the capstone RAG API.

Adapted from the course reference implementation
(ai-engineering-bootcamp/agentic-memory/memory_helpers.py::JsonMemoryStore) --
same get / replace / list shape, plus an explicit write gate: only a small,
named allow-list of stable facts can ever be persisted. Everything else
(retrieved chunks, one-off task details, raw model output) never touches this
file, per the Session 5 guidance that an agent remembering everything
remembers nothing useful.

Storage: one JSON file on local disk (MEMORY_STORE_PATH, default
memory_store.json next to this module). This is deliberately the simplest
option that satisfies "survive a process restart" -- see the README's memory
section for the honest caveat about what it does NOT survive (a fresh
container image on redeploy, if the host's disk isn't persistent).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Write gate: the only facts this store will ever persist. Everything else is
# rejected at write time -- keeps long-term memory small and high-signal
# instead of an unbounded dumping ground for anything the model decides.
ALLOWED_KEYS: dict[str, str] = {
    "preferred_name": "What the user wants to be called.",
    "preferred_language": "Language the user wants answers in.",
    "last_topic": "Subject of the user's most recent question, for continuity.",
}

_STORE_PATH = Path(os.getenv("MEMORY_STORE_PATH", Path(__file__).resolve().parent / "memory_store.json"))


class MemoryWriteRejected(ValueError):
    """Raised when a caller tries to persist a key outside ALLOWED_KEYS."""


def _read() -> dict[str, Any]:
    if not _STORE_PATH.exists():
        return {"human": {}, "audit": []}
    return json.loads(_STORE_PATH.read_text(encoding="utf-8"))


def _write(data: dict[str, Any]) -> None:
    _STORE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get(key: str) -> dict[str, Any] | None:
    """Return {'value', 'source', 'updated_at'} for one key, or None if unset."""

    return _read().get("human", {}).get(key)


def list_all() -> dict[str, dict[str, Any]]:
    """Return every currently-stored fact, keyed by name."""

    return dict(_read().get("human", {}))


def replace(key: str, value: str, source: str = "agent") -> dict[str, Any]:
    """Persist one fact. Only keys in ALLOWED_KEYS are accepted (the write gate)."""

    if key not in ALLOWED_KEYS:
        raise MemoryWriteRejected(
            f"'{key}' is not a durable-memory key. Allowed: {sorted(ALLOWED_KEYS)}"
        )
    data = _read()
    entry = {
        "value": value,
        "source": source,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    data.setdefault("human", {})[key] = entry
    data.setdefault("audit", []).append({"op": "replace", "key": key, **entry})
    _write(data)
    return entry


def clear() -> None:
    """Wipe all stored facts. Not exposed over the API -- local/debug use only."""

    _write({"human": {}, "audit": []})
