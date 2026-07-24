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
            "mode": str(knowledge_policy.get("mode") or "index").strip().lower(),
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
        "injection_overview": build_injection_optimization_overview(loader),
    }


def _is_inject_doc_file(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8")[:500]
    except OSError:
        return False
    return "inject: doc" in head.lower()


def _list_inject_doc_files(loader: SkillsBundleLoader) -> list[dict[str, Any]]:
    root = loader.root / "knowledge"
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.md")):
        if not _is_inject_doc_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = str(path.relative_to(loader.root)).replace("\\", "/")
        out.append({"path": rel, "chars": len(text), "status": "永不注入"})
    return out


def _skill_reference_paths(loader: SkillsBundleLoader, agent_id: str) -> list[str]:
    """SKILL.md references 里指向 knowledge 的路径（含仍挂着的 doc 长文）。"""
    try:
        entry = loader.get_role_entry(agent_id)
    except KeyError:
        return []
    skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
    skill_path = loader.root / skill_dir / "SKILL.md"
    if not skill_path.is_file():
        return []
    try:
        text = skill_path.read_text(encoding="utf-8")
    except OSError:
        return []
    fm = _parse_frontmatter(text)
    refs = [str(r) for r in (fm.get("references") or []) if isinstance(r, str)]
    resolved: list[str] = []
    for ref in refs:
        raw = ref.replace("\\", "/")
        if "knowledge/" not in raw:
            continue
        # ../../knowledge/foo.md → knowledge/foo.md
        idx = raw.find("knowledge/")
        rel = raw[idx:]
        path = (loader.root / rel).resolve()
        if path.is_file():
            resolved.append(rel)
    return resolved


def build_injection_optimization_overview(
    loader: SkillsBundleLoader | None = None,
) -> dict[str, Any]:
    """运维页「优化成果」：改前长文 vs 改后 exec，带可核对节省量。"""
    loader = loader or get_skills_loader()
    excluded_docs = _list_inject_doc_files(loader)
    excluded_by_path = {d["path"]: d for d in excluded_docs}
    excluded_total = sum(int(d["chars"]) for d in excluded_docs)

    rows: list[dict[str, Any]] = []
    for entry in loader.registry.get("roles") or []:
        agent_id = str(entry.get("agent_id") or "")
        if not agent_id.startswith("drama."):
            continue
        try:
            contract = loader.get_role_contract(agent_id)
            breakdown = build_prompt_breakdown(agent_id, settings={}, loader=loader)
        except Exception:
            continue

        knowledge_policy = contract.get("knowledge_policy") or {}
        module_policy = contract.get("module_policy") or {}
        manifest = breakdown.get("injection_manifest") or {}
        layers = breakdown.get("layers") or {}
        know_layer = layers.get("knowledge") if isinstance(layers, dict) else {}
        knowledge_after = int((know_layer or {}).get("chars") or 0)
        truncated = bool((know_layer or {}).get("truncated")) or any(
            isinstance(v, dict) and v.get("truncated") for v in (layers or {}).values()
        )

        # 改前：SKILL 仍引用的 inject:doc 长文全文合计（若当时全文注入）
        ref_paths = _skill_reference_paths(loader, agent_id)
        blocked_docs: list[dict[str, Any]] = []
        knowledge_before_docs = 0
        for rel in ref_paths:
            doc = excluded_by_path.get(rel)
            if not doc:
                # 再读一次确认
                path = loader.root / rel
                if path.is_file() and _is_inject_doc_file(path):
                    try:
                        chars = len(path.read_text(encoding="utf-8"))
                    except OSError:
                        continue
                    doc = {"path": rel, "chars": chars, "status": "永不注入"}
                else:
                    continue
            blocked_docs.append(doc)
            knowledge_before_docs += int(doc["chars"])

        know_included = list((manifest.get("knowledge") or {}).get("included") or [])
        exec_files: list[dict[str, Any]] = []
        for item in know_included:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or "").replace("\\", "/")
            if "-exec." not in path:
                continue
            exec_files.append(
                {
                    "path": path,
                    "chars": int(item.get("chars") or 0),
                    "status": "已注入",
                }
            )
        exec_chars = sum(int(e["chars"]) for e in exec_files)
        # 知识层节省：停注长文 − 现用 exec（同角色有对照时才有意义）
        knowledge_saved = max(0, knowledge_before_docs - exec_chars)
        system_chars = int(breakdown.get("system_total") or 0)
        # 若仍注入长文，system 还会再大 knowledge_saved
        system_if_docs = system_chars + knowledge_saved

        wins: list[str] = []
        if knowledge_saved > 0:
            wins.append(f"知识少灌 {knowledge_saved:,} 字")
        if exec_files:
            wins.append(f"改用 exec×{len(exec_files)}")
        if blocked_docs:
            wins.append(f"挡住长文×{len(blocked_docs)}")
        if bool(module_policy.get("evaluate_enable_when")):
            skipped = len((manifest.get("modules") or {}).get("skipped") or [])
            if skipped:
                wins.append(f"条件跳过模块×{skipped}")
        budget = int(knowledge_policy.get("max_chars") or 0)
        if budget > 0:
            wins.append(f"知识预算≤{budget:,}")

        rows.append(
            {
                "agent_id": agent_id,
                "name_zh": entry.get("name_zh") or agent_id,
                "system_chars": system_chars,
                "system_chars_if_docs": system_if_docs,
                "knowledge_before_chars": knowledge_before_docs,
                "knowledge_after_chars": knowledge_after,
                "knowledge_exec_chars": exec_chars,
                "knowledge_saved_chars": knowledge_saved,
                "blocked_docs": blocked_docs,
                "exec_files": exec_files,
                "modules_included": len(
                    (manifest.get("modules") or {}).get("included") or []
                ),
                "modules_skipped": len(
                    (manifest.get("modules") or {}).get("skipped") or []
                ),
                "evaluate_enable_when": bool(module_policy.get("evaluate_enable_when")),
                "knowledge_max_chars": budget,
                "truncated": truncated,
                "wins": wins,
                # 兼容旧前端字段
                "highlights": wins,
                "knowledge_exec_paths": [e["path"] for e in exec_files],
            }
        )

    rows.sort(key=lambda r: int(r.get("knowledge_saved_chars") or 0), reverse=True)
    saved_sum = sum(int(r.get("knowledge_saved_chars") or 0) for r in rows)
    exec_sum = sum(int(r.get("knowledge_exec_chars") or 0) for r in rows)
    roles_with_save = sum(1 for r in rows if int(r.get("knowledge_saved_chars") or 0) > 0)

    return {
        "title": "注入优化对照（改前长文 vs 改后 exec）",
        "summary": (
            f"仓库内 {len(excluded_docs)} 篇 inject:doc 长文共 {excluded_total:,} 字永不进 prompt；"
            f"有对照的角色合计少灌约 {saved_sum:,} 字（改用 exec {exec_sum:,} 字）。"
        ),
        "excluded_docs": excluded_docs,
        "excluded_docs_chars": excluded_total,
        "roles": rows,
        "totals": {
            "role_count": len(rows),
            "system_chars_sum": sum(int(r.get("system_chars") or 0) for r in rows),
            "knowledge_saved_sum": saved_sum,
            "exec_chars_sum": exec_sum,
            "excluded_docs_count": len(excluded_docs),
            "excluded_docs_chars": excluded_total,
            "roles_with_knowledge_save": roles_with_save,
            "roles_with_exec": sum(1 for r in rows if r.get("exec_files")),
            "roles_with_knowledge_budget": sum(
                1 for r in rows if int(r.get("knowledge_max_chars") or 0) > 0
            ),
            "roles_with_enable_when": sum(
                1 for r in rows if r.get("evaluate_enable_when")
            ),
            "roles_truncated": sum(1 for r in rows if r.get("truncated")),
        },
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


def _module_id_set(entries: Any) -> set[str]:
    if not isinstance(entries, list):
        return set()
    return {str(m.get("id") or "") for m in entries if isinstance(m, dict) and m.get("id")}


def _knowledge_path_set(entries: Any) -> set[str]:
    if not isinstance(entries, list):
        return set()
    return {
        str(m.get("path") or "")
        for m in entries
        if isinstance(m, dict) and m.get("path")
    }


def _any_truncated(manifest: dict[str, Any]) -> bool:
    layers = manifest.get("layers") or {}
    if isinstance(layers, dict):
        for stat in layers.values():
            if isinstance(stat, dict) and stat.get("truncated"):
                return True
    for key in ("rules", "knowledge", "modules"):
        block = manifest.get(key) or {}
        if isinstance(block, dict) and block.get("truncated"):
            return True
    return False


def diff_injection_manifests(
    dry: dict[str, Any],
    live: dict[str, Any],
) -> dict[str, Any]:
    """对比干跑与真实调用的 InjectionManifest（模块 / 知识 / 截断 / 字数）。"""
    dry_mods = _module_id_set((dry.get("modules") or {}).get("included"))
    live_mods = _module_id_set((live.get("modules") or {}).get("included"))
    dry_know = _knowledge_path_set((dry.get("knowledge") or {}).get("included"))
    live_know = _knowledge_path_set((live.get("knowledge") or {}).get("included"))
    dry_chars = int(dry.get("system_chars") or 0)
    live_chars = int(live.get("system_chars") or 0)
    mismatches: list[dict[str, Any]] = []
    if dry_mods != live_mods:
        mismatches.append(
            {
                "kind": "modules",
                "only_dry": sorted(dry_mods - live_mods),
                "only_live": sorted(live_mods - dry_mods),
            }
        )
    if dry_know != live_know:
        mismatches.append(
            {
                "kind": "knowledge",
                "only_dry": sorted(dry_know - live_know),
                "only_live": sorted(live_know - dry_know),
            }
        )
    dry_trunc = _any_truncated(dry)
    live_trunc = _any_truncated(live)
    if dry_trunc != live_trunc:
        mismatches.append(
            {
                "kind": "truncated",
                "dry": dry_trunc,
                "live": live_trunc,
            }
        )
    char_delta = abs(dry_chars - live_chars)
    if dry_chars > 0 and (char_delta > 2000 or char_delta / dry_chars > 0.1):
        mismatches.append(
            {
                "kind": "system_chars",
                "dry": dry_chars,
                "live": live_chars,
                "delta": live_chars - dry_chars,
            }
        )
    return {
        "matched": len(mismatches) == 0,
        "mismatches": mismatches,
        "dry_system_chars": dry_chars,
        "live_system_chars": live_chars,
        "dry_truncated": dry_trunc,
        "live_truncated": live_trunc,
        "dry_checksum": dry.get("checksum"),
        "live_checksum": live.get("checksum"),
    }


def fetch_latest_live_manifest(agent_id: str) -> dict[str, Any] | None:
    """取该角色最近一条带 injection_manifest 的调用。"""
    from apps.drama.models import DramaLlmCallLog

    qs = (
        DramaLlmCallLog.objects.filter(role=agent_id)
        .exclude(injection_manifest__isnull=True)
        .order_by("-created_at")
    )
    for log in qs[:20]:
        manifest = log.injection_manifest
        if isinstance(manifest, dict) and manifest.get("layers") is not None:
            return {
                "llm_log_id": str(log.id),
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "status": log.status,
                "injection_manifest": manifest,
            }
    return None


def build_live_injection_compare(
    agent_id: str,
    dry_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    """干跑 manifest vs 最近真实调用。"""
    if not isinstance(dry_manifest, dict):
        return {"available": False, "reason": "no_dry_manifest"}
    live = fetch_latest_live_manifest(agent_id)
    if not live:
        return {"available": False, "reason": "no_live_call"}
    diff = diff_injection_manifests(dry_manifest, live["injection_manifest"])
    return {
        "available": True,
        "llm_log_id": live["llm_log_id"],
        "created_at": live["created_at"],
        "status": live["status"],
        **diff,
    }


def build_injection_observation_todos(
    *,
    loader: SkillsBundleLoader | None = None,
    lookback: int = 30,
) -> list[dict[str, Any]]:
    """Inventory 只读待办：常 truncated / 干跑与最近调用 mismatch。"""
    from apps.drama.models import DramaLlmCallLog

    loader = loader or get_skills_loader()
    todos: list[dict[str, Any]] = []
    roles = [
        str(e.get("agent_id") or "")
        for e in (loader.registry.get("roles") or [])
        if e.get("agent_id") and str(e.get("agent_id")).startswith("drama.")
    ]
    for agent_id in roles:
        if not agent_id:
            continue
        recent = list(
            DramaLlmCallLog.objects.filter(role=agent_id)
            .exclude(injection_manifest__isnull=True)
            .order_by("-created_at")[:lookback]
        )
        trunc_count = 0
        for log in recent:
            m = log.injection_manifest
            if isinstance(m, dict) and _any_truncated(m):
                trunc_count += 1
        if trunc_count >= 2 or (
            len(recent) >= 1 and trunc_count == len(recent) and trunc_count > 0
        ):
            todos.append(
                {
                    "kind": "often_truncated",
                    "agent_id": agent_id,
                    "message": f"近 {len(recent)} 次调用中有 {trunc_count} 次预算截断",
                    "reason_zh": (
                        f"{agent_id} 最近 {len(recent)} 次里有 {trunc_count} 次知识/规则被预算截断，"
                        "可能丢硬约束。"
                    ),
                    "severity": "warn",
                    "count": trunc_count,
                    "sample_size": len(recent),
                    "actions": [
                        {
                            "kind": "roles",
                            "label": "去装配",
                            "query": {"tab": "roles", "role": agent_id},
                        },
                        {
                            "kind": "live",
                            "label": "看调用",
                            "query": {"tab": "live", "role": agent_id},
                        },
                    ],
                }
            )
        try:
            dry = build_prompt_breakdown(agent_id, settings={}, loader=loader)
            compare = build_live_injection_compare(
                agent_id, dry.get("injection_manifest")
            )
        except Exception:
            continue
        if compare.get("available") and not compare.get("matched"):
            log_id = compare.get("llm_log_id")
            actions: list[dict[str, Any]] = [
                {
                    "kind": "roles",
                    "label": "去装配",
                    "query": {"tab": "roles", "role": agent_id},
                }
            ]
            if log_id:
                actions.append(
                    {
                        "kind": "live",
                        "label": "看这次注入",
                        "query": {"tab": "live", "log_id": str(log_id)},
                    }
                )
            todos.append(
                {
                    "kind": "dry_live_mismatch",
                    "agent_id": agent_id,
                    "message": "干跑与最近真实调用注入清单不一致",
                    "reason_zh": (
                        f"{agent_id} 的干跑装配与最近一次真实调用不一致"
                        "（模块/知识/截断或字数漂移）。"
                    ),
                    "severity": "warn",
                    "llm_log_id": log_id,
                    "mismatches": compare.get("mismatches") or [],
                    "actions": actions,
                }
            )
    return todos
