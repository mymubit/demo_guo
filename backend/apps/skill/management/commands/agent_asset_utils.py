from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


DISCARD_PARTS = {".cache", "output", "test-output", "node_modules", "fixtures"}
SKIP_DIR_PARTS = {".git", "node_modules", ".idea", "__pycache__", "dist", "build"}
SKIP_FILE_NAMES = frozenset({
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package.json",
})


def should_skip_inventory_path(path: Path, root: Path) -> bool:
    if any(part in SKIP_DIR_PARTS for part in path.parts):
        return True
    rel = path.relative_to(root)
    if len(rel.parts) == 1 and path.name in SKIP_FILE_NAMES:
        return True
    return False


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_asset(path: Path) -> str:
    parts = {p.lower() for p in path.parts}
    name = path.name.lower()
    suffix = path.suffix.lower()
    text = path.as_posix().lower()
    if parts & DISCARD_PARTS:
        return "discard"
    if name == "skill.md":
        return "agent_skill_docs"
    if "reference-scripts" in text and suffix in {".md", ".txt"}:
        return "reference_scripts"
    if suffix == ".schema.json" or "schemas" in parts and suffix == ".json":
        return "schemas"
    if suffix == ".js" and (
        "detection" in parts
        or "drama-shared-detection" in parts
        or "runtime" in parts
        or name.startswith("verify-")
        or name.startswith("gate-")
    ):
        return "validators"
    if suffix in {".md", ".json"} and (
        "reference" in parts
        or "references" in parts
        or "templates" in parts
        or name == "node-llm-prompts.json"
    ):
        return "prompt_references"
    if suffix in {".md", ".json"} and ("knowledge" in parts or "config" in parts):
        return "rules"
    return "examples_and_fixtures" if suffix in {".json", ".md", ".txt"} else "discard"


def category_for_classification(classification: str) -> str:
    return {
        "agent_skill_docs": "prompt_section",
        "prompt_references": "knowledge",
        "rules": "rule",
        "schemas": "schema",
        "validators": "validator",
        "reference_scripts": "reference_script",
        "examples_and_fixtures": "example",
    }.get(classification, "knowledge")


def suggested_agent(path: Path) -> str:
    text = path.as_posix().lower()
    mapping = {
        # drama.* 新体系路径关键词 → agent_id
        "brief": "drama.topic-planner",
        "topic": "drama.topic-planner",
        "world": "drama.world-architect",
        "structure": "drama.plot-architect",
        "character": "drama.character-designer",
        "outline": "drama.plot-architect",
        "plot": "drama.plot-architect",
        "script": "drama.script-writer",
        "review": "drama.script-reviewer",
        "quality": "drama.quality-reporter",
        "score": "drama.quality-reporter",
        "compliance": "drama.compliance-guard",
    }
    for token, agent_id in mapping.items():
        if token in text:
            return agent_id
    return ""


def read_asset(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".json":
        try:
            return {"content_text": "", "content_json": json.loads(text)}
        except json.JSONDecodeError:
            return {"content_text": text, "content_json": {}}
    return {"content_text": text, "content_json": {}}


def iter_inventory(roots: Iterable[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for raw in roots:
        root = Path(raw).expanduser().resolve()
        if not root.exists():
            rows.append({
                "path": str(root),
                "root": str(root),
                "exists": False,
                "classification": "missing",
                "import_action": "error",
            })
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if should_skip_inventory_path(path, root):
                continue
            classification = classify_asset(path)
            rel = path.relative_to(root).as_posix()
            rows.append({
                "path": str(path),
                "root": str(root),
                "relative_path": rel,
                "size": path.stat().st_size,
                "checksum": file_checksum(path),
                "classification": classification,
                "suggested_agent": suggested_agent(path),
                "source_origin": root.name,
                "import_action": "discard" if classification == "discard" else "import",
            })
    return rows
