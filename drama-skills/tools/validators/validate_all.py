#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键运行 drama-skills/tools/validators 下核心 validate_* 脚本。

用法（在 drama-skills 根目录）:
  python tools/validators/validate_all.py

任一子校验非 0 退出码则本进程以 1 退出。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

VALIDATORS_DIR = Path(__file__).resolve().parent
ROOT = VALIDATORS_DIR.parents[1]

# 顺序：先契约/配置，再技能全库，再工作台与质检用例
_SCRIPTS = (
    "validate_config.py",
    "validate_theme_matrix.py",
    "validate_artifacts.py",
    "validate_workflow.py",
    "validate_skills.py",
    "validate_workbench.py",
    "validate_quality_cases.py",
)


def main() -> int:
    failed: list[str] = []
    for name in _SCRIPTS:
        path = VALIDATORS_DIR / name
        if not path.is_file():
            print(f"[SKIP] 缺少 {name}", flush=True)
            failed.append(name)
            continue
        print(f"\n======== {name} ========", flush=True)
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
        )
        if proc.returncode != 0:
            print(f"[FAIL] {name} exit={proc.returncode}", flush=True)
            failed.append(name)
        else:
            print(f"[OK] {name}", flush=True)

    print("\n======== validate_all 汇总 ========", flush=True)
    if failed:
        print("失败: " + ", ".join(failed), flush=True)
        return 1
    print("全部通过", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
