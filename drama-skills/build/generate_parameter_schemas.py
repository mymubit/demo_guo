#!/usr/bin/env python3
"""从 contracts/parameters.yaml 生成 JSON Schema 定义文件。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.parameter_schema_generator import ROOT, generated_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="生成参数 JSON Schema 定义")
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅校验已提交生成物是否与契约一致（不写文件）",
    )
    args = parser.parse_args()
    artifacts = generated_artifacts(ROOT)
    if args.check:
        drift = []
        for relative_path, expected in sorted(artifacts.items()):
            target = ROOT / relative_path
            if not target.exists():
                drift.append(f"缺少生成物: {relative_path}")
                continue
            actual = target.read_text(encoding="utf-8")
            if actual != expected:
                drift.append(f"生成物漂移: {relative_path}")
        if drift:
            for message in drift:
                print(f"ERROR {message}")
            print(f"\n生成物校验失败：{len(drift)} 处漂移。请运行 python build/generate_parameter_schemas.py")
            return 1
        print("生成物与 contracts/parameters.yaml 一致")
        return 0

    for relative_path, content in sorted(artifacts.items()):
        target = ROOT / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(relative_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
