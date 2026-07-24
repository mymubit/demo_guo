from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {"pending", "migrate", "split", "merge", "rewrite", "archive", "reject"}


def main() -> int:
    inventory = json.loads((ROOT / "migration" / "inventory.json").read_text(encoding="utf-8"))
    mapping = json.loads((ROOT / "migration" / "mapping.json").read_text(encoding="utf-8"))
    inventory_paths = {item["path"] for item in inventory["files"]}
    mapped = {item["source"]: item for item in mapping["mappings"]}
    errors = []

    missing = sorted(inventory_paths - set(mapped))
    extra = sorted(set(mapped) - inventory_paths)
    if missing:
        errors.append(f"missing mappings: {missing[:10]}")
    if extra:
        errors.append(f"unknown mappings: {extra[:10]}")

    for source, item in mapped.items():
        disposition = item.get("disposition")
        if disposition not in ALLOWED:
            errors.append(f"{source}: invalid disposition {disposition!r}")
        if disposition not in {"pending", "archive", "reject"} and not item.get("targets"):
            errors.append(f"{source}: {disposition} requires at least one V6 target")
        for target in item.get("targets", []):
            if not target.startswith("v6/"):
                errors.append(f"{source}: target must be under v6/: {target}")

    counts = Counter(item.get("disposition", "missing") for item in mapped.values())
    report = {
        "inventory_files": len(inventory_paths),
        "mapped_files": len(mapped),
        "dispositions": dict(sorted(counts.items())),
        "classified_coverage": round((len(mapped) - counts.get("pending", 0)) / max(len(inventory_paths), 1), 6),
        "verified_coverage": round(sum(bool(item.get("verified")) for item in mapped.values()) / max(len(inventory_paths), 1), 6),
        "errors": errors,
    }
    (ROOT / "migration" / "coverage-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
