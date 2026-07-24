from __future__ import annotations

import json
import os
import re
import tempfile
from copy import deepcopy
from pathlib import Path


class JournalError(RuntimeError):
    pass


class CallJournal:
    """Store one atomically replaced replay document per call."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_id(call_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", call_id):
            raise JournalError("invalid call_id")
        return call_id

    def path(self, call_id: str) -> Path:
        return self.root / f"{self._safe_id(call_id)}.json"

    def save(self, envelope: dict) -> Path:
        target = self.path(envelope["call_id"])
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(envelope, handle, ensure_ascii=False, sort_keys=True, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return target

    def load(self, call_id: str) -> dict:
        target = self.path(call_id)
        if not target.exists():
            raise JournalError(f"unknown call_id: {call_id}")
        try:
            return deepcopy(json.loads(target.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            raise JournalError(f"invalid journal entry {call_id}: {exc}") from exc
