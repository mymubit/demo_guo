from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def classify(source: str) -> tuple[str, list[str], str]:
    path = Path(source)
    parts = path.parts
    first = parts[0]

    if first in {".trae-html-share-packages", ".uploads", "drama-skills-architecture", "drama-skills-optimization"}:
        return "archive", [], "保留为 V5 工作材料或生成视图，不进入 V6 运行时。"
    if source in {"EVOLUTION_LOG.md", "ROLE-DESIGN-ANALYSIS.md", "REPOSITORY.md"}:
        return "archive", [], "保留为 V5 历史与设计证据。"
    if first == "knowledge":
        target = f"v6/sources/{'/'.join(parts[1:])}"
        return "migrate", [target], "迁移为可溯源领域材料，不直接作为运行时规则。"
    if first == "inspirations":
        target = f"v6/sources/inspirations/{'/'.join(parts[1:])}"
        return "migrate", [target], "迁移为创意来源材料，保持与原子规则隔离。"
    if first == "foundation":
        if len(parts) > 1 and parts[1] == "rules":
            return "split", ["v6/atoms/", "v6/evaluations/atomic-rules/"], "拆分为单义原子规则及其正反边界测试。"
        if len(parts) > 1 and parts[1] in {"constraints", "presets"}:
            return "rewrite", [f"v6/{parts[1]}/"], "重写为独立数值/枚举契约并保留来源引用。"
        return "rewrite", ["v6/constraints/theme/"], "重建为 V6 题材与组合约束。"
    if first == "modules":
        if path.name == "catalog.yaml":
            return "rewrite", ["v6/capabilities/catalog.yaml"], "按 V6 无状态能力目录重建。"
        return "split", ["v6/atoms/", "v6/capabilities/", "v6/evaluations/capabilities/"], "提取原子规则并重建无状态能力及测试。"
    if first in {"roles", "drama-master", "drama-intake"}:
        return "rewrite", ["v6/operations/", "v6/capabilities/"], "按操作而非角色重建；旧执行说明不直接复用。"
    if first == "contracts":
        return "rewrite", ["v6/contracts/", "v6/artifacts/"], "按调用事务、操作与 V6 产物重新定义契约。"
    if first == "schemas":
        return "rewrite", ["v6/artifacts/", "v6/contracts/"], "审计字段语义后重写 Schema，不机械复制宽松结构。"
    if first == "orchestration":
        return "rewrite", ["v6/workflows/"], "按 V6 操作事务重建流程，禁止调用 V5 角色状态机。"
    if first == "runtime":
        return "rewrite", ["v6/engine/"], "使用 V6 单一路径执行内核替换。"
    if first in {"workbench", "manifest", "registry.yaml"}:
        return "rewrite", ["v6/manifest.yaml", "v6/contracts/"], "围绕 V6 操作、调用追踪和版本边界重建。"
    if first in {"quality", "eval"}:
        return "rewrite", ["v6/evaluations/"], "迁移意图并重写为原子、能力、操作和端到端分层评测。"
    if first == "tools":
        return "rewrite", ["v6/tools/"], "仅迁移仍符合 V6 契约的工具逻辑。"
    if first == "optimizations":
        return "archive", [], "V5 优化产物仅归档；V6 优化必须基于新评测重建。"
    if first in {"scripts", ".github"}:
        return "rewrite", ["v6/tools/"], "按 V6 发布与校验边界重建。"
    if source in {"README.md", "INTAKE_PROTOCOL.md"}:
        return "rewrite", ["v6/sources/system/"], "保留有效意图，按 V6 对象模型重写。"
    if source in {"requirements-dev.txt", ".gitignore"}:
        return "merge", ["v6/requirements-dev.txt"], "合并进入 V6 工具依赖或仓库治理配置。"
    return "archive", [], "未进入 V6 运行时；保留在冻结快照供后续人工复核。"


def main() -> int:
    mapping_path = ROOT / "migration" / "mapping.json"
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    for item in data["mappings"]:
        if item.get("disposition") != "pending":
            continue
        disposition, targets, decision = classify(item["source"])
        item.update(
            {
                "disposition": disposition,
                "targets": targets,
                "decision": decision,
                "verified": False,
            }
        )
    mapping_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Classified {len(data['mappings'])} V5 files; semantic verification remains explicit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
