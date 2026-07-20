# -*- coding: utf-8 -*-
"""角色 / 原子技能装配库存与 prompt 分层字数（只读透明化）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.drama.services.condition_eval import evaluate_condition, module_enable_context
from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.services.skills_loader import (
    SkillsBundleLoader,
    _parse_frontmatter,
    _knowledge_platform_allows,
    list_knowledge_catalog_files,
    get_skills_loader,
)

# 库存默认 dry-run：无题材时用占位四轴，仅用于规则/契约层字数统计（模块 enable_when 仍用真实 settings）
_DEFAULT_GENRE_MATRIX = {
    "emotion": "revenge",
    "identity": "reborn",
    "conflict": "family",
    "world": "modern",
}


def _settings_with_theme_fallback(settings: dict[str, Any] | None) -> dict[str, Any]:
    """为 collect_rules / PromptBuilder 补齐题材，避免空设定直接失败。"""
    merged = dict(settings or {})
    matrix = merged.get("genre_matrix")
    axes = ("emotion", "identity", "conflict", "world")
    if isinstance(matrix, dict) and all(str(matrix.get(a) or "").strip() for a in axes):
        return merged
    if str(merged.get("preset_theme_code") or "").strip():
        return merged
    base = dict(matrix) if isinstance(matrix, dict) else {}
    for axis, value in _DEFAULT_GENRE_MATRIX.items():
        if not str(base.get(axis) or "").strip():
            base[axis] = value
    merged["genre_matrix"] = base
    return merged


def _file_chars(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8"))


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _knowledge_ref_paths(loader: SkillsBundleLoader, agent_id: str) -> list[Path]:
    entry = loader.get_role_entry(agent_id)
    skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
    skill_path = loader.root / skill_dir / "SKILL.md"
    if not skill_path.exists():
        return []
    fm = _parse_frontmatter(skill_path.read_text(encoding="utf-8"))
    refs = [str(r) for r in (fm.get("references") or []) if isinstance(r, str)]
    knowledge_refs = [
        r
        for r in refs
        if "/knowledge/" in r.replace("\\", "/") or r.startswith("../../knowledge/")
    ]
    paths: list[Path] = []
    seen: set[Path] = set()
    for ref in knowledge_refs:
        path = (loader.root / skill_dir / ref).resolve()
        if path.is_dir() and (path / "catalog.yaml").is_file():
            candidates = list_knowledge_catalog_files(path / "catalog.yaml")
        elif path.name == "catalog.yaml" and path.is_file():
            candidates = list_knowledge_catalog_files(path)
        elif path.exists() and path.is_file():
            candidates = [path]
        else:
            candidates = []
        for item in candidates:
            if item not in seen:
                seen.add(item)
                paths.append(item)
    return paths


def _module_enable_state(
    loader: SkillsBundleLoader,
    module_id: str,
    *,
    evaluate: bool,
    settings: dict[str, Any] | None,
) -> tuple[bool, str | None]:
    """返回 (enabled, skip_reason)。"""
    catalog = loader.modules_catalog.get("modules") or {}
    meta = catalog.get(module_id) or {}
    expr = meta.get("enable_when")
    if not evaluate or not expr:
        return True, None
    context = module_enable_context(settings)
    try:
        if evaluate_condition(str(expr), context):
            return True, None
    except ValueError as exc:
        return False, f"条件无效: {exc}"
    return False, f"未满足 enable_when: {expr}"


def build_role_attachments(
    loader: SkillsBundleLoader,
    agent_id: str,
    *,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = loader.get_role_entry(agent_id)
    contract = loader.get_role_contract(agent_id)
    skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
    skill_md_path = loader.root / skill_dir / "SKILL.md"
    catalog = loader.modules_catalog.get("modules") or {}
    module_policy = contract.get("module_policy") or {}
    evaluate = bool(module_policy.get("evaluate_enable_when"))
    rule_policy = contract.get("rule_policy") or {}
    knowledge_policy = contract.get("knowledge_policy") or {}

    modules_out: list[dict[str, Any]] = []
    for module_id in list(contract.get("modules") or []):
        meta = catalog.get(module_id) or {}
        mod_path = loader.root / "modules" / f"{module_id}.md"
        enabled, reason = _module_enable_state(
            loader, module_id, evaluate=evaluate, settings=settings
        )
        modules_out.append(
            {
                "id": module_id,
                "label_zh": meta.get("label_zh") or module_id,
                "path": f"modules/{module_id}.md",
                "file_chars": _file_chars(mod_path),
                "enable_when": meta.get("enable_when"),
                "enabled_default": enabled,
                "skip_reason": reason,
                "domain": meta.get("domain"),
                "kind": meta.get("kind"),
            }
        )

    rules_text = loader.collect_rules(
        agent_id,
        _settings_with_theme_fallback(settings),
        max_chars=int(rule_policy.get("max_chars") or 0),
    )
    knowledge_paths = _knowledge_ref_paths(loader, agent_id)
    knowledge_refs = []
    for path in knowledge_paths:
        rel = _rel(loader.root, path)
        in_douyin_pack = "douyin-formulas" in rel.replace("\\", "/")
        platform_ok = _knowledge_platform_allows(path.name, "generic") and not in_douyin_pack
        item: dict[str, Any] = {
            "path": rel,
            "file_chars": _file_chars(path),
            "enabled_default": platform_ok,
        }
        if in_douyin_pack:
            item["skip_reason"] = "仅 target_platform=douyin 且题材命中 catalog 时注入"
            item["enable_when"] = "target_platform == 'douyin' + genre match"
        else:
            token = None
            name_l = path.name.lower()
            for t in ("douyin", "kuaishou", "wechat", "bilibili", "xiaohongshu"):
                if t in name_l:
                    token = t
                    break
            if token and not platform_ok:
                item["skip_reason"] = f"仅 target_platform={token} 时注入"
                item["enable_when"] = f"target_platform == '{token}'"
        knowledge_refs.append(item)

    fewshots_path = loader.root / skill_dir / "fewshots.v1.yaml"
    anti_path = loader.root / skill_dir / "anti-examples.yaml"
    fewshots: dict[str, Any] | None = None
    anti: dict[str, Any] | None = None
    if fewshots_path.exists():
        data = loader._load_yaml(str(fewshots_path.relative_to(loader.root)))
        fewshots = {
            "path": f"{skill_dir}/fewshots.v1.yaml",
            "count": len(list(data.get("fewshots") or [])),
            "file_chars": _file_chars(fewshots_path),
        }
    if anti_path.exists():
        data = loader._load_yaml(str(anti_path.relative_to(loader.root)))
        anti = {
            "path": f"{skill_dir}/anti-examples.yaml",
            "count": len(list(data.get("examples") or [])),
            "file_chars": _file_chars(anti_path),
        }

    skill_chars = _file_chars(skill_md_path)
    module_chars = sum(m["file_chars"] for m in modules_out)
    knowledge_chars = sum(k["file_chars"] for k in knowledge_refs)
    few_chars = int((fewshots or {}).get("file_chars") or 0)
    anti_chars = int((anti or {}).get("file_chars") or 0)
    rules_chars = len(rules_text)

    return {
        "skill_md": {
            "path": f"{skill_dir}/SKILL.md",
            "file_chars": skill_chars,
        },
        "modules": modules_out,
        "module_policy": {
            "evaluate_enable_when": evaluate,
            "max_chars": int(module_policy.get("max_chars") or 0),
        },
        "rule_policy": {
            "scopes": list(rule_policy.get("scopes") or []),
            "sections": [str(s) for s in (rule_policy.get("sections") or [])],
            "max_chars": int(rule_policy.get("max_chars") or 0),
            "file_chars": rules_chars,
        },
        "knowledge_refs": knowledge_refs,
        "knowledge_policy": {
            "max_chars": int(knowledge_policy.get("max_chars") or 0),
        },
        "fewshots": fewshots,
        "anti_examples": anti,
        "file_total_chars": (
            skill_chars
            + module_chars
            + knowledge_chars
            + few_chars
            + anti_chars
            + rules_chars
        ),
    }


def build_skills_inventory(loader: SkillsBundleLoader | None = None) -> dict[str, Any]:
    loader = loader or get_skills_loader()
    catalog = loader.modules_catalog.get("modules") or {}
    roles_out: list[dict[str, Any]] = []
    mounted_by: dict[str, list[str]] = {mid: [] for mid in catalog}
    knowledge_index: dict[str, set[str]] = {}
    section_index: dict[str, set[str]] = {}

    for entry in loader.registry.get("roles") or []:
        agent_id = str(entry.get("agent_id") or "")
        if not agent_id:
            continue
        try:
            attachments = build_role_attachments(loader, agent_id, settings=None)
        except (KeyError, FileNotFoundError):
            continue
        for mod in attachments["modules"]:
            mounted_by.setdefault(mod["id"], []).append(agent_id)
        for ref in attachments["knowledge_refs"]:
            knowledge_index.setdefault(ref["path"], set()).add(agent_id)
        for section in attachments["rule_policy"]["sections"]:
            section_index.setdefault(section, set()).add(agent_id)
        roles_out.append(
            {
                "agent_id": agent_id,
                "name_zh": entry.get("name_zh") or agent_id,
                "dept": entry.get("dept"),
                "role_tier": entry.get("role_tier"),
                "skill_dir": entry.get("skill_dir"),
                "attachments": attachments,
                "file_total_chars": attachments["file_total_chars"],
            }
        )

    modules_out: list[dict[str, Any]] = []
    for module_id, meta in catalog.items():
        if not isinstance(meta, dict):
            continue
        target = [str(r) for r in (meta.get("target_roles") or [])]
        mounted = mounted_by.get(module_id) or []
        mismatch = sorted(set(target) ^ set(mounted))
        mod_path = loader.root / "modules" / f"{module_id}.md"
        modules_out.append(
            {
                "id": module_id,
                "label_zh": meta.get("label_zh") or module_id,
                "domain": meta.get("domain"),
                "kind": meta.get("kind"),
                "lifecycle": meta.get("lifecycle"),
                "path": f"modules/{module_id}.md",
                "file_chars": _file_chars(mod_path),
                "enable_when": meta.get("enable_when"),
                "target_roles": target,
                "mounted_by": mounted,
                "mismatch": mismatch,
            }
        )

    knowledge_files = [
        {
            "path": path,
            "file_chars": _file_chars(loader.root / path),
            "referenced_by_roles": sorted(roles),
        }
        for path, roles in sorted(knowledge_index.items())
    ]
    rule_sections = [
        {
            "section": section,
            "used_by_roles": sorted(roles),
        }
        for section, roles in sorted(section_index.items())
    ]

    return {
        "skills_bundle_version": loader.bundle_version,
        "roles": roles_out,
        "modules": modules_out,
        "knowledge_files": knowledge_files,
        "rule_sections": rule_sections,
    }


def build_prompt_breakdown(
    agent_id: str,
    *,
    settings: dict[str, Any] | None = None,
    loader: SkillsBundleLoader | None = None,
) -> dict[str, Any]:
    """组装分层字数；不返回 prompt 全文。与 PromptBuilder InjectionManifest 同源。"""
    loader = loader or get_skills_loader()
    settings = settings or {}
    had_complete_theme = False
    matrix = settings.get("genre_matrix")
    if isinstance(matrix, dict) and all(
        str(matrix.get(a) or "").strip() for a in ("emotion", "identity", "conflict", "world")
    ):
        had_complete_theme = True
    elif str(settings.get("preset_theme_code") or "").strip():
        had_complete_theme = True
    entry = loader.get_role_entry(agent_id)
    theme_settings = _settings_with_theme_fallback(settings)

    # 模块 enable 用真实 settings；题材轴用 fallback，避免空设定崩掉
    build_settings = dict(settings)
    build_settings["genre_matrix"] = theme_settings["genre_matrix"]
    if theme_settings.get("preset_theme_code") and not build_settings.get("preset_theme_code"):
        build_settings["preset_theme_code"] = theme_settings["preset_theme_code"]

    _system, _user, manifest = PromptBuilder(loader=loader).build(
        agent_id,
        settings=build_settings,
        workflow_state={},
        artifacts={},
    )

    catalog = loader.modules_catalog.get("modules") or {}

    def _module_row(item: dict[str, Any]) -> dict[str, Any]:
        mid = str(item.get("id") or "")
        meta = catalog.get(mid) or {}
        body = loader.load_module(mid) if mid else ""
        row = {
            "id": mid,
            "label_zh": item.get("label_zh") or meta.get("label_zh") or mid,
            "file_chars": len(body),
            "chars": int(item.get("chars") or 0),
            "enable_when": item.get("enable_when", meta.get("enable_when")),
            "mode": item.get("mode"),
        }
        if item.get("reason"):
            row["reason"] = item["reason"]
        return row

    layers = {
        key: {"chars": int((stat or {}).get("chars") or 0), "truncated": bool((stat or {}).get("truncated"))}
        for key, stat in (manifest.get("layers") or {}).items()
        if isinstance(stat, dict)
    }

    return {
        "agent_id": agent_id,
        "name_zh": entry.get("name_zh") or agent_id,
        "project_id": None,
        "settings_mode": "project" if settings else "default",
        "layers": layers,
        "system_total": int(manifest.get("system_chars") or 0),
        "modules_included": [
            _module_row(m) for m in (manifest.get("modules") or {}).get("included") or []
        ],
        "modules_skipped": [
            _module_row(m) for m in (manifest.get("modules") or {}).get("skipped") or []
        ],
        "knowledge_included": list((manifest.get("knowledge") or {}).get("included") or []),
        "knowledge_skipped": list((manifest.get("knowledge") or {}).get("skipped") or []),
        "injection_manifest": manifest,
        "theme_fallback": not had_complete_theme,
    }


def _resolve_under_root(loader: SkillsBundleLoader, relative: str) -> Path:
    """解析技能仓相对路径，拒绝越界。"""
    rel = relative.replace("\\", "/").lstrip("/")
    if not rel or ".." in rel.split("/"):
        raise ValueError("非法路径")
    root = loader.root.resolve()
    path = (loader.root / rel).resolve()
    if not str(path).startswith(str(root)):
        raise ValueError("路径越出技能仓")
    if not path.is_file():
        raise FileNotFoundError(f"文件不存在: {rel}")
    return path


def read_skills_content(
    *,
    kind: str,
    module_id: str | None = None,
    agent_id: str | None = None,
    path: str | None = None,
    loader: SkillsBundleLoader | None = None,
) -> dict[str, Any]:
    """按需读取技能仓正文（模块 / SKILL / 相对路径 / 角色规则组装）。"""
    loader = loader or get_skills_loader()
    kind = (kind or "").strip()

    if kind == "module":
        mid = (module_id or "").strip()
        if not mid:
            raise ValueError("缺少 module id")
        catalog = loader.modules_catalog.get("modules") or {}
        if mid not in catalog:
            raise KeyError(f"未知原子技能: {mid}")
        body = loader.load_module(mid)
        rel = f"modules/{mid}.md"
        return {
            "kind": "module",
            "id": mid,
            "label_zh": (catalog.get(mid) or {}).get("label_zh") or mid,
            "path": rel,
            "content": body,
            "chars": len(body),
        }

    if kind == "role_skill":
        aid = (agent_id or "").strip()
        if not aid:
            raise ValueError("缺少 agent_id")
        entry = loader.get_role_entry(aid)
        skill_dir = entry.get("skill_dir") or f"roles/{aid.replace('.', '-')}"
        rel = f"{skill_dir}/SKILL.md"
        file_path = _resolve_under_root(loader, rel)
        content = file_path.read_text(encoding="utf-8")
        return {
            "kind": "role_skill",
            "agent_id": aid,
            "path": rel,
            "content": content,
            "chars": len(content),
        }

    if kind == "path":
        rel = (path or "").strip().replace("\\", "/")
        if not rel:
            raise ValueError("缺少 path")
        file_path = _resolve_under_root(loader, rel)
        content = file_path.read_text(encoding="utf-8")
        return {
            "kind": "path",
            "path": rel,
            "content": content,
            "chars": len(content),
        }

    if kind == "role_rules":
        aid = (agent_id or "").strip()
        if not aid:
            raise ValueError("缺少 agent_id")
        contract = loader.get_role_contract(aid)
        rule_policy = contract.get("rule_policy") or {}
        text = loader.collect_rules(
            aid,
            _settings_with_theme_fallback({}),
            max_chars=int(rule_policy.get("max_chars") or 0),
        )
        return {
            "kind": "role_rules",
            "agent_id": aid,
            "path": None,
            "content": text,
            "chars": len(text),
            "scopes": list(rule_policy.get("scopes") or []),
            "sections": [str(s) for s in (rule_policy.get("sections") or [])],
        }

    raise ValueError(f"不支持的 kind: {kind}")


def build_role_bundle_content(
    agent_id: str,
    *,
    loader: SkillsBundleLoader | None = None,
) -> dict[str, Any]:
    """角色全部挂载正文：SKILL / 模块 / 知识 / fewshots / 反例 / 规则组装。"""
    loader = loader or get_skills_loader()
    entry = loader.get_role_entry(agent_id)
    contract = loader.get_role_contract(agent_id)
    skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
    catalog = loader.modules_catalog.get("modules") or {}

    skill = read_skills_content(kind="role_skill", agent_id=agent_id, loader=loader)
    modules_out: list[dict[str, Any]] = []
    for mid in list(contract.get("modules") or []):
        meta = catalog.get(mid) or {}
        body = loader.load_module(mid)
        modules_out.append(
            {
                "id": mid,
                "label_zh": meta.get("label_zh") or mid,
                "path": f"modules/{mid}.md",
                "content": body,
                "chars": len(body),
                "enable_when": meta.get("enable_when"),
            }
        )

    knowledge_out: list[dict[str, Any]] = []
    for path in _knowledge_ref_paths(loader, agent_id):
        rel = _rel(loader.root, path)
        text = path.read_text(encoding="utf-8")
        knowledge_out.append({"path": rel, "content": text, "chars": len(text)})

    fewshots = None
    few_path = loader.root / skill_dir / "fewshots.v1.yaml"
    if few_path.exists():
        text = few_path.read_text(encoding="utf-8")
        fewshots = {
            "path": f"{skill_dir}/fewshots.v1.yaml",
            "content": text,
            "chars": len(text),
        }

    anti = None
    anti_path = loader.root / skill_dir / "anti-examples.yaml"
    if anti_path.exists():
        text = anti_path.read_text(encoding="utf-8")
        anti = {
            "path": f"{skill_dir}/anti-examples.yaml",
            "content": text,
            "chars": len(text),
        }

    rules = read_skills_content(kind="role_rules", agent_id=agent_id, loader=loader)

    return {
        "agent_id": agent_id,
        "name_zh": entry.get("name_zh") or agent_id,
        "skill_md": skill,
        "modules": modules_out,
        "knowledge": knowledge_out,
        "fewshots": fewshots,
        "anti_examples": anti,
        "rules": rules,
    }
