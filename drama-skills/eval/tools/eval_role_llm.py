# -*- coding: utf-8 -*-
"""角色 LLM 评测：离线 fixture 回放 + 可选在线调用。

用法:
  python eval/tools/eval_role_llm.py --roles topic-director,story-bible --offline
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

ROOT = Path(__file__).resolve().parents[2]
EVAL_ROOT = ROOT / "eval"
FIXTURES = ROOT / "tools/fixtures/artifacts/valid-artifacts.json"
REPORTS = EVAL_ROOT / "reports"

ROLE_SLUGS = {
    "topic-director": "drama.topic-director",
    "story-bible": "drama.story-bible",
    "script-scorer": "drama.script-scorer",
    "compliance-guard": "drama.compliance-guard",
}

ROLE_ARTIFACT = {
    "drama.topic-director": "project_brief",
    "drama.story-bible": "story_bible",
    "drama.script-scorer": "quality_report",
    "drama.compliance-guard": "compliance_report",
}


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def deep_get(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def run_check(check: Dict[str, Any], payload: Dict[str, Any]) -> Optional[str]:
    ctype = check.get("type")
    path = str(check.get("path") or "")
    value = deep_get(payload, path) if path else None
    if ctype == "field_nonempty":
        if value is None or (isinstance(value, str) and not value.strip()):
            return f"{path} 为空"
        return None
    if ctype == "list_of_strings":
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            return f"{path} 须为字符串数组"
        return None
    if ctype == "enum":
        allowed = check.get("values") or []
        if value not in allowed:
            return f"{path}={value} 不在 {allowed}"
        return None
    if ctype == "object_keys":
        keys = check.get("keys") or []
        if not isinstance(value, dict):
            return f"{path} 须为对象"
        missing = [k for k in keys if k not in value]
        if missing:
            return f"{path} 缺少键 {missing}"
        return None
    if ctype == "list_length":
        expected = int(check.get("length") or 0)
        if not isinstance(value, list) or len(value) != expected:
            return f"{path} 长度须为 {expected}"
        return None
    if ctype == "list_min":
        minimum = int(check.get("min") or 0)
        if not isinstance(value, list) or len(value) < minimum:
            return f"{path} 至少 {minimum} 项"
        return None
    return f"未知检查类型 {ctype}"


def evaluate_case(
    case: Dict[str, Any],
    *,
    fixtures: Dict[str, Any],
    rubrics: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    role = case["role"]
    artifact_key = ROLE_ARTIFACT.get(role) or case.get("artifact_key")
    payload = case.get("fixture_response")
    if payload is None:
        payload = fixtures.get(artifact_key)
    if not isinstance(payload, dict):
        return {"id": case.get("id"), "ok": False, "errors": ["缺少 fixture_response"]}

    errors: List[str] = []
    assertions = case.get("assertions") or {}
    if assertions.get("schema", True):
        # 轻量：必填字段存在即视为结构基线；完整 schema 由后端单测覆盖
        for field in assertions.get("required_fields") or []:
            if deep_get(payload, field) in (None, "", []):
                errors.append(f"required_fields 失败: {field}")

    rubric_ids = assertions.get("rubric") or []
    rubric = rubrics.get(artifact_key) or {}
    check_map = {c["id"]: c for c in (rubric.get("checks") or []) if c.get("id")}
    for rid in rubric_ids:
        check = check_map.get(rid)
        if not check:
            errors.append(f"未知 rubric: {rid}")
            continue
        msg = run_check(check, payload)
        if msg:
            errors.append(msg)

    return {
        "id": case.get("id"),
        "role": role,
        "artifact_key": artifact_key,
        "ok": not errors,
        "errors": errors,
    }


def load_cases(role_slugs: List[str]) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for slug in role_slugs:
        directory = EVAL_ROOT / "cases" / slug
        if not directory.is_dir():
            print(f"WARN 缺少 case 目录: {directory}", file=sys.stderr)
            continue
        for path in sorted(directory.glob("*.yaml")):
            data = load_yaml(path)
            if not data.get("role"):
                data["role"] = ROLE_SLUGS.get(slug, slug)
            cases.append(data)
    return cases


def load_rubrics() -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for path in (EVAL_ROOT / "rubrics").glob("*.yaml"):
        data = load_yaml(path)
        key = data.get("artifact_key") or path.stem
        result[str(key)] = data
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Drama role LLM eval")
    parser.add_argument(
        "--roles",
        default="topic-director,story-bible",
        help="逗号分隔角色 slug",
    )
    parser.add_argument("--offline", action="store_true", default=True)
    parser.add_argument("--online", action="store_true", default=False)
    args = parser.parse_args()
    if args.online:
        print("在线模式请通过后端 GenerationService 集成；本脚本默认离线 fixture 回归。")

    slugs = [s.strip() for s in args.roles.split(",") if s.strip()]
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    rubrics = load_rubrics()
    cases = load_cases(slugs)
    if not cases:
        print("没有可运行的 case")
        return 1

    results = [evaluate_case(case, fixtures=fixtures, rubrics=rubrics) for case in cases]
    passed = sum(1 for r in results if r["ok"])
    summary = {
        "total": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 4) if results else 0.0,
        "failed": [r for r in results if not r["ok"]],
        "results": results,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"评测完成: {passed}/{len(results)} 通过 → {out.relative_to(ROOT)}")
    for failed in summary["failed"]:
        print(f"FAIL {failed['id']}: {failed['errors']}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
