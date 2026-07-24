from __future__ import annotations

from copy import deepcopy
import json
import os
import tempfile
from pathlib import Path
from threading import RLock


class VersionConflict(RuntimeError):
    pass


class InMemoryArtifactStore:
    """Reference store implementing optimistic, all-or-nothing V6 commits."""

    def __init__(self, artifacts: dict[str, dict] | None = None):
        self._artifacts = deepcopy(artifacts or {})
        self._lock = RLock()

    def versions(self, names: list[str]) -> dict[str, object]:
        with self._lock:
            return {name: self._artifacts.get(name, {}).get("version") for name in names}

    def commit(
        self,
        writes: list[str],
        candidate: dict,
        expected_versions: dict[str, object],
        commit_id: str | None = None,
    ) -> dict:
        with self._lock:
            actual = self.versions(list(expected_versions))
            if actual != expected_versions:
                raise VersionConflict(f"base versions changed: expected={expected_versions}, actual={actual}")
            missing = [name for name in writes if name not in candidate]
            if missing:
                raise ValueError(f"candidate is missing declared writes: {missing}")
            next_versions = {}
            replacements = {}
            for name in writes:
                current = self._artifacts.get(name, {}).get("version")
                next_version = 1 if current is None else current + 1
                replacements[name] = {"version": next_version, "value": deepcopy(candidate[name])}
                next_versions[name] = next_version
            self._artifacts.update(replacements)
            return {"committed": writes, "versions": next_versions}

    def snapshot(self) -> dict:
        with self._lock:
            return deepcopy(self._artifacts)


class FileArtifactStore:
    """Persist all artifacts in one atomically replaced state document."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        if not self.path.exists():
            self._replace({"format_version": 1, "artifacts": {}, "commits": {}})

    def _read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _replace(self, state: dict) -> None:
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(state, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def versions(self, names: list[str]) -> dict[str, object]:
        with self._lock:
            state = self._read()
            return {name: state["artifacts"].get(name, {}).get("version") for name in names}

    def commit(
        self,
        writes: list[str],
        candidate: dict,
        expected_versions: dict[str, object],
        commit_id: str | None = None,
    ) -> dict:
        if not commit_id:
            raise ValueError("persistent commits require commit_id")
        with self._lock:
            state = self._read()
            prior = state["commits"].get(commit_id)
            if prior is not None:
                return deepcopy(prior)
            actual = {name: state["artifacts"].get(name, {}).get("version") for name in expected_versions}
            if actual != expected_versions:
                raise VersionConflict(f"base versions changed: expected={expected_versions}, actual={actual}")
            missing = [name for name in writes if name not in candidate]
            if missing:
                raise ValueError(f"candidate is missing declared writes: {missing}")
            next_versions = {}
            for name in writes:
                current = state["artifacts"].get(name, {}).get("version")
                next_version = 1 if current is None else current + 1
                state["artifacts"][name] = {"version": next_version, "value": deepcopy(candidate[name])}
                next_versions[name] = next_version
            receipt = {"commit_id": commit_id, "committed": list(writes), "versions": next_versions}
            state["commits"][commit_id] = receipt
            self._replace(state)
            return deepcopy(receipt)

    def snapshot(self) -> dict:
        with self._lock:
            return deepcopy(self._read()["artifacts"])
