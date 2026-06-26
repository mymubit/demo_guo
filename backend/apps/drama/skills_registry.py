# -*- coding: utf-8 -*-
"""从 drama-skills/ Git SSOT 加载角色、编排与规则元数据。"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from django.conf import settings

logger = logging.getLogger(__name__)

SKILL_VERSION = "drama-skills-v4.0"

# 部门 → DramaStage（与 apps.drama.constants.DramaStage 值对齐）
DEPT_TO_DRAMA_STAGE: Dict[str, str] = {
    "strategy": "strategy",
    "worldbuilding": "worldbuilding",
    "plot_engine": "plot_design",
    "writing": "writing",
    "review": "review",
    "polish": "polish",
    "production": "production",
    "ops": "compliance",
}

DELIVERY_AGENT_IDS = frozenset({"drama.delivery-tool"})
QUALITY_AGENT_ID = "drama.script-scorer"


def get_drama_skills_root() -> Path:
    configured = getattr(settings, "DRAMA_SKILLS_ROOT", "") or ""
    if configured:
        return Path(configured)
    base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd()))
    return base_dir.parent / "drama-skills"


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[skills_registry] 无法解析 %s: %s", path, exc)
        return {}
    return data if isinstance(data, dict) else {}


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        match = re.match(r"^---\s*\n.*?\n---\s*\n", text, flags=re.DOTALL)
        if match:
            return text[match.end():].strip()
    return text.strip()


@lru_cache(maxsize=1)
def load_registry() -> Dict[str, Any]:
    root = get_drama_skills_root()
    data = _read_yaml(root / "registry.yaml")
    if not data:
        logger.warning("[skills_registry] registry.yaml 未找到或为空: %s", root)
    return data


def clear_registry_cache() -> None:
    load_registry.cache_clear()
    build_role_defaults.cache_clear()
    load_agent_runtime_policies.cache_clear()
    load_agent_tier1_sections.cache_clear()
    load_script_format_constraints.cache_clear()
    load_quality_scoring_constraints.cache_clear()
    load_artifact_chunk_constraints.cache_clear()
    get_quality_dimensions.cache_clear()
    get_artifact_chunk_map.cache_clear()
    build_agent_stream_config.cache_clear()
    get_composite_agent_ids.cache_clear()
    get_agent_alias_map.cache_clear()
    from apps.drama.theme_matrix_service import clear_theme_matrix_cache

    clear_theme_matrix_cache()


@lru_cache(maxsize=1)
def load_agent_runtime_policies() -> Dict[str, Dict[str, Any]]:
    root = get_drama_skills_root()
    data = _read_yaml(root / "foundation" / "constraints" / "agent-runtime.yaml")
    agents = data.get("agents") or {}
    if isinstance(agents, dict):
        return {str(k): dict(v) for k, v in agents.items() if isinstance(v, dict)}
    logger.warning("[skills_registry] agent-runtime.yaml 未找到或为空")
    return {}


@lru_cache(maxsize=1)
def get_composite_agent_ids() -> frozenset[str]:
    registry = load_registry()
    composite = {
        str(item["agent_id"])
        for item in (registry.get("roles") or [])
        if isinstance(item, dict)
        and item.get("agent_id")
        and str(item.get("role_tier") or "") in {"composite", "tool"}
    }
    return frozenset(composite)


@lru_cache(maxsize=1)
def get_agent_alias_map() -> Dict[str, str]:
    registry = load_registry()
    aliases = registry.get("aliases") or {}
    if not isinstance(aliases, dict):
        return {}
    visible = set(get_visible_agent_ids())
    result: Dict[str, str] = {}
    for old_id, new_id in aliases.items():
        old_key = str(old_id or "").strip()
        new_key = str(new_id or "").strip()
        if old_key and new_key in visible:
            result[old_key] = new_key
    return result


def normalize_agent_id(agent_id: str) -> str:
    key = str(agent_id or "").strip()
    return get_agent_alias_map().get(key, key)


@lru_cache(maxsize=1)
def load_script_format_constraints() -> Dict[str, Any]:
    root = get_drama_skills_root()
    return _read_yaml(root / "foundation" / "constraints" / "script-format.yaml")


@lru_cache(maxsize=1)
def load_quality_scoring_constraints() -> Dict[str, Any]:
    root = get_drama_skills_root()
    data = _read_yaml(root / "foundation" / "constraints" / "quality-scoring.yaml")
    if not data:
        logger.warning("[skills_registry] quality-scoring.yaml 未找到或为空")
    return data


@lru_cache(maxsize=1)
def get_quality_dimensions() -> List[Dict[str, Any]]:
    """G-Eval 十维评分维度（key/name/weight/desc）。"""
    data = load_quality_scoring_constraints()
    raw = data.get("dimensions") or []
    dimensions: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        name = str(item.get("name") or "").strip()
        if not key or not name:
            continue
        try:
            weight = float(item.get("weight") or 0)
        except (TypeError, ValueError):
            weight = 0.0
        dimensions.append({
            "key": key,
            "name": name,
            "weight": weight,
            "desc": str(item.get("desc") or "").strip(),
        })
    return dimensions


def get_quality_grade_thresholds() -> Dict[str, int]:
    """综合等级阈值 S/A/B/C（与 scoring-core.yaml 一致）。"""
    data = load_quality_scoring_constraints()
    thresholds = data.get("grade_thresholds")
    if isinstance(thresholds, dict) and thresholds:
        return {str(k): int(v) for k, v in thresholds.items()}
    script_fmt = load_script_format_constraints().get("quality_grades") or {}
    if isinstance(script_fmt, dict) and script_fmt:
        return {str(k): int(v) for k, v in script_fmt.items()}
    return {"S": 90, "A": 80, "B": 75, "C": 60}


def _normalize_chunk_config(raw: Dict[str, Any], artifact_key: str) -> Dict[str, Any]:
    array_keys = raw.get("array_keys") or []
    if isinstance(array_keys, str):
        array_keys = [array_keys]
    return {
        "kind": str(raw.get("kind") or artifact_key),
        "array_keys": tuple(str(k) for k in array_keys),
    }


@lru_cache(maxsize=1)
def load_artifact_chunk_constraints() -> Dict[str, Any]:
    root = get_drama_skills_root()
    data = _read_yaml(root / "foundation" / "constraints" / "artifact-chunk-map.yaml")
    if not data:
        logger.warning("[skills_registry] artifact-chunk-map.yaml 未找到或为空")
    return data


@lru_cache(maxsize=1)
def get_artifact_chunk_map() -> Dict[str, Dict[str, Any]]:
    """artifact_key → {kind, array_keys}。"""
    data = load_artifact_chunk_constraints()
    artifacts = data.get("artifacts") or {}
    mapping: Dict[str, Dict[str, Any]] = {}
    if isinstance(artifacts, dict):
        for artifact_key, raw in artifacts.items():
            if isinstance(raw, dict):
                mapping[str(artifact_key)] = _normalize_chunk_config(raw, str(artifact_key))
    return mapping


@lru_cache(maxsize=1)
def build_agent_stream_config() -> Dict[str, Dict[str, Any]]:
    """agent_id / artifact_key → 流式分片配置（由 registry 主产物键推导）。"""
    artifact_map = get_artifact_chunk_map()
    agent_map: Dict[str, Dict[str, Any]] = {}
    for role in build_role_defaults():
        agent_id = str(role.get("agent_id") or "")
        artifact_key = str(role.get("default_output_artifact_key") or "")
        if agent_id and artifact_key and artifact_key in artifact_map:
            agent_map[agent_id] = artifact_map[artifact_key]
    for artifact_key, config in artifact_map.items():
        agent_map.setdefault(artifact_key, config)
    return agent_map


def get_array_artifact_keys() -> frozenset[str]:
    data = load_artifact_chunk_constraints()
    raw = data.get("array_artifact_keys") or []
    if isinstance(raw, list) and raw:
        return frozenset(str(k) for k in raw)
    return frozenset(get_artifact_chunk_map().keys())


def get_pipeline_result_key_map() -> Dict[str, str]:
    data = load_artifact_chunk_constraints()
    mapping = data.get("pipeline_result_keys") or {}
    if isinstance(mapping, dict) and mapping:
        return {str(k): str(v) for k, v in mapping.items()}
    return {
        "project_brief": "project_brief",
        "world_setting": "world_setting",
        "character_bible": "character_bible",
        "series_outline": "series_outline",
        "episode_scripts": "scripts",
        "quality_report": "quality_report",
        "compliance_report": "compliance_report",
    }


@lru_cache(maxsize=1)
def load_agent_tier1_sections() -> Dict[str, List[str]]:
    """解析 knowledge/knowledge-sections.md 中的角色 ↔ Section 映射表。"""
    path = get_drama_skills_root() / "knowledge" / "knowledge-sections.md"
    if not path.is_file():
        logger.warning("[skills_registry] knowledge-sections.md 未找到")
        return {}
    mapping: Dict[str, List[str]] = {}
    in_table = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if "角色" in line and "Section" in line and line.startswith("## "):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("| drama."):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        agent_id = cells[0]
        sections_raw = cells[1]
        if not agent_id.startswith("drama."):
            continue
        if sections_raw.startswith("（") or "compliance_block" in sections_raw:
            mapping[agent_id] = []
            continue
        mapping[agent_id] = [part.strip() for part in sections_raw.split(",") if part.strip()]
    return mapping


def get_primary_artifact_map() -> Dict[str, str]:
    return {
        role["agent_id"]: role["default_output_artifact_key"]
        for role in build_role_defaults()
        if role.get("agent_id") and role.get("default_output_artifact_key")
    }


def build_agent_phase_map(track_mode: str = "fast") -> Dict[str, str]:
    """从 orchestration YAML（专家轨）或 registry.dept（快速轨）推导 agent→阶段。"""
    if track_mode == "expert":
        plan = load_orchestration("expert-track")
        mapping: Dict[str, str] = {}
        for phase in plan.get("phases") or []:
            phase_code = str(phase.get("phase") or "")
            for agent_id in phase.get("agents") or []:
                mapping[str(agent_id)] = phase_code
        return mapping

    mapping = {}
    for entry in load_registry().get("roles") or []:
        if not isinstance(entry, dict):
            continue
        agent_id = entry.get("agent_id")
        dept = entry.get("dept")
        if agent_id and dept:
            mapping[str(agent_id)] = DEPT_TO_DRAMA_STAGE.get(str(dept), "strategy")
    return mapping


def get_departments() -> List[Dict[str, Any]]:
    registry = load_registry()
    departments = registry.get("departments") or []
    return [
        {"code": str(item["code"]), "name_zh": str(item["name_zh"]), "order": int(item["order"])}
        for item in departments
        if isinstance(item, dict) and item.get("code")
    ]


def get_fast_track_agent_ids() -> List[str]:
    registry = load_registry()
    agents = registry.get("fast_track_agents") or []
    return [str(agent_id) for agent_id in agents if agent_id]


def get_visible_agent_ids() -> List[str]:
    registry = load_registry()
    roles = registry.get("roles") or []
    return [str(item["agent_id"]) for item in roles if isinstance(item, dict) and item.get("agent_id")]


def get_workspace_order_map() -> Dict[str, int]:
    registry = load_registry()
    mapping: Dict[str, int] = {}
    for item in registry.get("roles") or []:
        if not isinstance(item, dict):
            continue
        agent_id = item.get("agent_id")
        order = item.get("workspace_order")
        if agent_id and order is not None:
            mapping[str(agent_id)] = int(order)
    return mapping


def load_role_yaml(skill_dir: str) -> Dict[str, Any]:
    root = get_drama_skills_root()
    rel = (skill_dir or "").replace("\\", "/").strip("/")
    return _read_yaml(root / rel / "role.yaml")


def load_skill_markdown(skill_dir: str) -> str:
    root = get_drama_skills_root()
    rel = (skill_dir or "").replace("\\", "/").strip("/")
    skill_path = root / rel / "SKILL.md"
    if not skill_path.is_file():
        return ""
    return _strip_frontmatter(skill_path.read_text(encoding="utf-8"))


def build_system_prompt(skill_dir: str, role_yaml: Dict[str, Any]) -> str:
    body = load_skill_markdown(skill_dir)
    if body:
        return body
    role_desc = str(role_yaml.get("role") or role_yaml.get("description") or "").strip()
    name_zh = str(role_yaml.get("name_zh") or "").strip()
    if role_desc and name_zh:
        return f"你是专业的短剧{name_zh}。{role_desc}"
    return role_desc


def _resolve_tier(agent_id: str, role_tier: str, fast_track: bool) -> int:
    composite_ids = get_composite_agent_ids()
    if agent_id in composite_ids or role_tier in {"composite", "tool"}:
        return 2
    if fast_track:
        return 1
    return 2


def build_role_default(entry: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = str(entry["agent_id"])
    skill_dir = str(entry.get("skill_dir") or entry.get("role_dir") or "")
    role_yaml = load_role_yaml(skill_dir) if skill_dir else {}
    merged = {**role_yaml, **{k: v for k, v in entry.items() if v is not None}}

    fast_track_ids = set(get_fast_track_agent_ids())
    is_fast_track = agent_id in fast_track_ids or bool(merged.get("fast_track"))
    role_tier = str(merged.get("role_tier") or ("composite" if agent_id in get_composite_agent_ids() else "core"))

    input_contract = merged.get("input_contract") or {}
    if not isinstance(input_contract, dict):
        input_contract = {}
    output_contract = merged.get("output_contract") or {}
    if not isinstance(output_contract, dict):
        output_contract = {}
    if not output_contract.get("schema_version") and merged.get("schema_version"):
        output_contract = {
            **output_contract,
            "schema_version": merged["schema_version"],
        }
    if not output_contract.get("artifacts") and merged.get("default_output_artifact_key"):
        output_contract = {
            **output_contract,
            "artifacts": [merged["default_output_artifact_key"]],
        }

    description = str(
        merged.get("role")
        or merged.get("description")
        or role_yaml.get("role")
        or ""
    ).strip()

    return {
        "agent_id": agent_id,
        "name": str(merged.get("name") or role_yaml.get("name") or agent_id),
        "name_zh": str(merged.get("name_zh") or role_yaml.get("name_zh") or agent_id),
        "description": description,
        "dept": str(merged.get("dept") or role_yaml.get("dept") or ""),
        "workspace_order": int(merged.get("workspace_order") or role_yaml.get("workspace_order") or 999),
        "default_output_artifact_key": str(
            merged.get("default_output_artifact_key")
            or role_yaml.get("default_output_artifact_key")
            or (output_contract.get("artifacts") or [""])[0]
        ),
        "input_contract": input_contract,
        "output_contract": output_contract,
        "runtime_policy": load_agent_runtime_policies().get(agent_id, {}),
        "system_prompt": build_system_prompt(skill_dir, role_yaml),
        "fast_track": is_fast_track,
        "tier": _resolve_tier(agent_id, role_tier, is_fast_track),
        "is_composite": agent_id in get_composite_agent_ids() or role_tier in {"composite", "tool"},
        "modules": list(merged.get("modules") or []),
        "skill_dir": skill_dir,
        "schema_version": str(
            merged.get("schema_version")
            or output_contract.get("schema_version")
            or ""
        ),
    }


@lru_cache(maxsize=1)
def build_role_defaults() -> List[Dict[str, Any]]:
    registry = load_registry()
    roles: List[Dict[str, Any]] = []
    for entry in registry.get("roles") or []:
        if not isinstance(entry, dict) or not entry.get("agent_id"):
            continue
        roles.append(build_role_default(entry))
    roles.sort(key=lambda item: (item.get("workspace_order", 999), item.get("agent_id", "")))
    return roles


def load_orchestration(track_name: str) -> Dict[str, Any]:
    """track_name: fast-track | expert-track"""
    root = get_drama_skills_root()
    filename = track_name if track_name.endswith(".yaml") else f"{track_name}.yaml"
    return _read_yaml(root / "orchestration" / filename)


def get_entry_plan(track_mode: str = "fast") -> Dict[str, Any]:
    if track_mode == "expert":
        plan = load_orchestration("expert-track")
    elif track_mode == "ip_adapt":
        plan = load_orchestration("ip-adapt")
    else:
        plan = load_orchestration("fast-track")
    if not plan:
        return _fallback_entry_plan(track_mode)
    return plan


def _fallback_entry_plan(track_mode: str) -> Dict[str, Any]:
    if track_mode == "expert":
        return {
            "entry_type": "expert_track",
            "label": "专家通道",
            "description": "标准主链后追加宣发交付工具，适合商业精品项目",
            "phases": [
                {"phase": "strategy", "label": "选题定调", "agents": ["drama.topic-director"]},
                {"phase": "worldbuilding", "label": "人物关系", "agents": ["drama.character-relations"]},
                {"phase": "plot_design", "label": "全剧架构", "agents": ["drama.series-architect"]},
                {"phase": "episode_design", "label": "分集设计", "agents": ["drama.episode-designer"]},
                {"phase": "writing", "label": "正文创作", "agents": ["drama.script-writer"]},
                {"phase": "polish", "label": "返修精修", "agents": ["drama.revision-master"]},
                {"phase": "review", "label": "独立评分", "agents": ["drama.script-scorer"]},
                {"phase": "compliance", "label": "合规审查", "agents": ["drama.compliance-guard"]},
                {"phase": "production", "label": "宣发交付", "agents": ["drama.delivery-tool"]},
            ],
        }
    return {
        "entry_type": "fast_track",
        "label": "标准创作通道",
        "description": "6个生产角色 + 2个独立裁判，适合高效产出剧本并保持质量闭环",
        "recommended_agents": get_fast_track_agent_ids(),
        "optional_agents": [],
    }


def iter_foundation_rule_files() -> List[Path]:
    root = get_drama_skills_root() / "foundation" / "rules"
    if not root.is_dir():
        return []
    files = sorted(root.glob("*.yaml"))
    files.extend(sorted((root / "genres").glob("*.yaml")))
    return files


def parse_foundation_rule_file(path: Path) -> List[Dict[str, Any]]:
    data = _read_yaml(path)
    if not data:
        return []

    tier = int(data.get("tier") or 0)
    genre_key = str(data.get("genre_key") or "").strip()
    version_tag = str(data.get("version") or SKILL_VERSION)
    source_note = f"drama-skills:{path.relative_to(get_drama_skills_root()).as_posix()}"

    rows: List[Dict[str, Any]] = []
    for index, item in enumerate(data.get("items") or []):
        if not isinstance(item, dict):
            continue
        rule_key = str(item.get("rule_key") or "").strip()
        section = str(item.get("section") or "").strip()
        body = str(item.get("body") or "").strip()
        if not rule_key or not section or not body:
            continue

        scope_type_raw = str(item.get("scope_type") or "").strip().lower()
        scope_key = str(item.get("scope_key") or genre_key or "").strip()

        if tier == 1 or scope_type_raw in ("", "global"):
            scope_type = "global"
            scope_key = ""
        elif tier == 2 or scope_type_raw == "genre":
            scope_type = "genre"
            scope_key = scope_key or genre_key
        elif tier == 3 or scope_type_raw in ("agent", "node"):
            scope_type = "node"
            scope_key = scope_key or str(item.get("scope_key") or "")
        elif tier == 4:
            scope_type = "global"
            scope_key = ""
        else:
            scope_type = "global"
            scope_key = ""

        rows.append({
            "rule_key": rule_key,
            "tier": tier or int(item.get("tier") or 1),
            "scope_type": scope_type,
            "scope_key": scope_key,
            "section": section,
            "title": str(item.get("title") or rule_key)[:512],
            "body": body,
            "priority": int(item.get("priority") or 100),
            "sort_order": index,
            "version_tag": version_tag,
            "source_note": source_note,
        })
    return rows
