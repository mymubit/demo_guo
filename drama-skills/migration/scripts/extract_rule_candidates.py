from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RULE_ROOT = ROOT / "foundation" / "rules"
CONSTRAINT_REF = re.compile(r"foundation/constraints/[A-Za-z0-9_./-]+(?:#[A-Za-z0-9_.{}-]+)?")
NUMBER = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?(?:%|秒|集|次|句|分钟)?")
TOKEN = re.compile(r"[A-Za-z0-9_.-]+|[\u4e00-\u9fff]{2,}")


def consumers(rule_key: str) -> list[str]:
    found = []
    for root_name in ("roles", "modules"):
        for path in (ROOT / root_name).rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".yml"}:
                continue
            try:
                if rule_key in path.read_text(encoding="utf-8"):
                    found.append(path.relative_to(ROOT).as_posix())
            except UnicodeDecodeError:
                pass
    return sorted(found)


def normalized_tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN.findall(text) if len(token) > 1}


def main() -> int:
    candidates = []
    for path in sorted(RULE_ROOT.rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for index, item in enumerate(data.get("items") or []):
            body = str(item.get("body") or item.get("description") or "").strip()
            key = str(item.get("rule_key") or f"unkeyed-{index}")
            relative = path.relative_to(ROOT).as_posix()
            candidates.append(
                {
                    "candidate_id": "candidate." + hashlib.sha1(f"{relative}:{key}".encode()).hexdigest()[:12],
                    "legacy_rule_key": key,
                    "title": item.get("title", ""),
                    "section": item.get("section", ""),
                    "body": body,
                    "source": relative,
                    "source_ref": item.get("source_ref"),
                    "constraint_refs": sorted(set(CONSTRAINT_REF.findall(body))),
                    "numeric_literals": NUMBER.findall(body),
                    "known_consumers": consumers(key),
                    "migration_status": "needs-semantic-split",
                }
            )

    duplicate_pairs = []
    token_cache = {item["candidate_id"]: normalized_tokens(item["body"]) for item in candidates}
    for i, left in enumerate(candidates):
        left_tokens = token_cache[left["candidate_id"]]
        for right in candidates[i + 1 :]:
            right_tokens = token_cache[right["candidate_id"]]
            union = left_tokens | right_tokens
            if not union:
                continue
            score = len(left_tokens & right_tokens) / len(union)
            if score >= 0.45 or (
                left["section"] and left["section"] == right["section"] and left["numeric_literals"] and right["numeric_literals"]
            ):
                duplicate_pairs.append(
                    {
                        "left": left["candidate_id"],
                        "right": right["candidate_id"],
                        "similarity": round(score, 4),
                        "reason": "text-overlap" if score >= 0.45 else "same-section-with-numeric-literals",
                    }
                )

    numeric_by_section = defaultdict(list)
    for item in candidates:
        if item["numeric_literals"]:
            numeric_by_section[item["section"]].append(
                {
                    "candidate_id": item["candidate_id"],
                    "source": item["source"],
                    "values": item["numeric_literals"],
                    "constraint_refs": item["constraint_refs"],
                }
            )

    report = {
        "version": 1,
        "source_files": len({item["source"] for item in candidates}),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    conflicts = {
        "version": 1,
        "duplicate_candidates": duplicate_pairs,
        "numeric_review_by_section": {key: value for key, value in sorted(numeric_by_section.items()) if key},
    }
    (ROOT / "migration" / "rule-candidates.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "migration" / "rule-conflict-candidates.json").write_text(
        json.dumps(conflicts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Extracted {len(candidates)} rule candidates from {report['source_files']} files; "
        f"flagged {len(duplicate_pairs)} duplicate/conflict pairs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
