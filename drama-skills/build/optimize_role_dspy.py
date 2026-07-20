# -*- coding: utf-8 -*-
"""可选：用 DSPy 对 topic-director / story-bible 做 few-shot 打样优化。

前置：eval/cases 已就绪；本脚本不进入 Django 生产依赖。
安装（仅优化环境）: pip install dspy-ai pyyaml

用法:
  python build/optimize_role_dspy.py --role topic-director --dry-run
  python build/optimize_role_dspy.py --role topic-director --write
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVAL_CASES = ROOT / "eval" / "cases"
ROLE_DIRS = {
    "topic-director": ROOT / "roles" / "drama-topic-director",
    "story-bible": ROOT / "roles" / "drama-story-bible",
}


def load_cases(slug: str, limit: int = 20) -> List[Dict[str, Any]]:
    directory = EVAL_CASES / slug
    cases: List[Dict[str, Any]] = []
    for path in sorted(directory.glob("*.yaml"))[:limit]:
        cases.append(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    return cases


def build_fewshots(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """从 eval case 抽取可人工审阅的 few-shot 草稿（无需 DSPy 也可生成）。"""
    shots = []
    for case in cases[:8]:
        settings = case.get("settings") or {}
        response = case.get("fixture_response") or {}
        # 压缩演示字段
        if case.get("role") == "drama.topic-director":
            demo_out = {
                k: response.get(k)
                for k in (
                    "title",
                    "core_idea",
                    "first_episode_hook",
                    "paywall_direction",
                    "blockbuster_factors",
                    "compliance_risk",
                )
                if k in response
            }
        else:
            demo_out = {
                k: response.get(k)
                for k in ("drama_title", "logline", "synopsis")
                if k in response
            }
        shots.append(
            {
                "case_id": case.get("id"),
                "input": {
                    "title": settings.get("title"),
                    "entry_type": settings.get("entry_type"),
                    "core_idea": settings.get("core_idea"),
                    "genre_matrix": settings.get("genre_matrix"),
                },
                "output": demo_out,
            }
        )
    return {
        "version": "1.0.0",
        "source": "eval/cases offline fixtures",
        "note": "人工审阅后再被 PromptBuilder 引用；禁止无审自动覆盖 SKILL.md",
        "fewshots": shots,
    }


def try_dspy_optimize(slug: str, cases: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    try:
        import dspy  # type: ignore
    except ImportError:
        return None

    # 最小可运行占位：把 fewshot 选择交给 BootstrapFewShot 需要真实 LM；
    # 无 API Key 时仅返回 None，由调用方回退到 fixture fewshots。
    _ = dspy
    _ = cases
    print("已检测到 dspy，但未配置 LM；回退为 fixture fewshots 草稿。")
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=sorted(ROLE_DIRS.keys()), required=True)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--write", action="store_true", default=False)
    parser.add_argument(
        "--provider-dir",
        default="generic",
        help="写入 optimizations/<provider>/ 子目录名",
    )
    args = parser.parse_args()
    slug = args.role
    cases = load_cases(slug)
    if len(cases) < 5:
        print(f"case 不足: {slug} 仅 {len(cases)} 条")
        return 1

    optimized = try_dspy_optimize(slug, cases)
    payload = optimized or build_fewshots(cases)

    role_dir = ROLE_DIRS[slug]
    out_default = role_dir / "fewshots.v1.yaml"
    opt_dir = ROOT / "optimizations" / args.provider_dir / slug
    opt_dir.mkdir(parents=True, exist_ok=True)
    out_provider = opt_dir / "fewshots.v1.yaml"

    text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    if args.write:
        out_default.write_text(text, encoding="utf-8")
        out_provider.write_text(text, encoding="utf-8")
        print(f"已写入 {out_default.relative_to(ROOT)}")
        print(f"已写入 {out_provider.relative_to(ROOT)}")
    else:
        print(text[:800])
        print("… dry-run 结束；加 --write 落盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())
