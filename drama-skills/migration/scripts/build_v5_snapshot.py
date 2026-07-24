from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_ROOTS = {"v6", "migration", "versions", ".git"}
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".sh", ".txt"}
PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.-])((?:foundation|knowledge|modules|roles|contracts|schemas|"
    r"orchestration|runtime|workbench|manifest|quality|eval|inspirations|tools)/"
    r"[A-Za-z0-9_./-]+)"
)


def category(path: Path) -> str:
    first = path.parts[0]
    if path.name == "SKILL.md":
        return "skill"
    if first in {"foundation", "knowledge", "modules", "roles", "contracts", "schemas"}:
        return first
    if first in {"orchestration", "runtime", "workbench", "manifest"}:
        return "runtime-configuration"
    if first in {"quality", "eval"}:
        return "evaluation"
    if first == "tools":
        return "tooling"
    return "repository"


def source_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] in EXCLUDED_ROOTS:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def references(path: Path) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    return sorted({match.rstrip("`'\".,;:)") for match in PATH_PATTERN.findall(text)})


def main() -> int:
    files = source_files()
    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    entries = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        content = path.read_bytes()
        entries.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "category": category(path.relative_to(ROOT)),
                "references": references(path),
            }
        )

    versions_dir = ROOT / "versions" / "v5"
    migration_dir = ROOT / "migration"
    versions_dir.mkdir(parents=True, exist_ok=True)
    migration_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "snapshot": "v5-working-tree",
        "frozen_at": frozen_at,
        "file_count": len(entries),
        "total_bytes": sum(item["bytes"] for item in entries),
        "files": entries,
    }
    (versions_dir / "freeze-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (migration_dir / "inventory.json").write_text(
        json.dumps({"version": 1, "source_snapshot": "v5-working-tree", "files": entries}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    mapping_path = migration_dir / "mapping.json"
    existing = {}
    if mapping_path.exists():
        existing_data = json.loads(mapping_path.read_text(encoding="utf-8"))
        existing = {item["source"]: item for item in existing_data.get("mappings", [])}
    mappings = []
    for entry in entries:
        mappings.append(
            existing.get(
                entry["path"],
                {
                    "source": entry["path"],
                    "source_sha256": entry["sha256"],
                    "disposition": "pending",
                    "targets": [],
                    "decision": "",
                    "verified": False,
                },
            )
        )
    mapping_path.write_text(
        json.dumps({"version": 1, "source_snapshot": "v5-working-tree", "mappings": mappings}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    archive_path = versions_dir / "v5-working-tree.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())

    print(f"Frozen {len(entries)} V5 files into {archive_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
