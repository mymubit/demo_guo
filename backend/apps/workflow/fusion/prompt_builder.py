# -*- coding: utf-8 -*-
"""
从 SSOT（project-config + schema + skill-rules）构建 LLM 提示词。

System prompt 组装顺序（技能总典四层）：
  [角色定位]  node-llm-prompts.json → role + outputInstruction（每节点独特部分）
  [Tier1]     skill-rules/tier1-iron-rules.json → 全局铁律（按节点最小化提取）
  [Tier2]     skill-rules/tier2-genre-rules.json → 品类专属规则（热加载，按 genre）
  [Tier3]     skill-rules/tier3-workflow-rules.json → 节点验收标准（热加载，按 node_id）

规则不写在这里，也不写在 node-llm-prompts.json 里。
如需修改规则，只编辑 skill-rules/ 目录下的对应 JSON 文件。
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from django.conf import settings

from .config_loader import FusionSkillConfig, get_fusion_config
from .registry import FusionNodeRegistry
from .ssot_catalog import FusionSsotCatalog
from .upstream_context import dedupe_upstream_aliases, pick_upstream_for_sub_skill

_HANDBOOK_MAX_CHARS = 8000
_REFERENCE_MAX_CHARS = 4000


def _extract_theme(upstream: Dict[str, Any]) -> Optional[str]:
    """从 upstream 中提取 theme，兼容不同 artifact 结构。"""
    for key in ("theme", "projectTheme", "genre"):
        val = upstream.get(key)
        if val and isinstance(val, str):
            return val.strip().lower()
    brief = upstream.get("projectBrief") or upstream.get("project_brief") or {}
    if isinstance(brief, dict):
        for key in ("theme", "projectTheme", "genre"):
            val = brief.get(key)
            if val and isinstance(val, str):
                return val.strip().lower()
    return None


def _extract_creation_entry(upstream: Dict[str, Any]) -> str:
    """从 upstream 中提取 creationEntry，优先 project_brief 中的值。"""
    for key in ("creationEntry", "creation_entry"):
        val = upstream.get(key)
        if val and isinstance(val, str):
            return val.strip()
    brief = upstream.get("projectBrief") or upstream.get("project_brief") or {}
    if isinstance(brief, dict):
        for key in ("creationEntry", "creation_entry"):
            val = brief.get(key)
            if val and isinstance(val, str):
                return val.strip()
    return "from-scratch"


# node11/12 多创作入口专属提示词注入（FUSION-ADAPTATION.md 待完成项）
_ENTRY_PROMPT_HINTS: Dict[str, str] = {
    "novel-adaptation": (
        "【创作入口：网文改编 node-11】\n"
        "本项目基于小说原文改编，project_brief.novelSourceText 包含源文本。\n"
        "核心要求：\n"
        "- 保留原著核心人物关系与主线情节节点，禁止随意删减主角人设\n"
        "- 将原著散文式叙述压缩为短剧集段节奏（每集70-100字场景+对白，单集1-3场戏）\n"
        "- 优先保留原著中爽感/反转/虐心节点，压缩铺垫性描写\n"
        "- 若 novelSourceText 超过当前节点需求，仅处理本节点相关章节"
    ),
    "from-reference": (
        "【创作入口：风格对标 node-12】\n"
        "本项目参考热门作品叙事节奏创作，project_brief.referenceWork 说明了参考对象。\n"
        "核心要求：\n"
        "- 只学节奏结构与情绪曲线，禁止复制原作台词、人名、具体情节\n"
        "- project_brief.referenceFingerprint.forbidDialogueCopy=true，原创性检测全程开启\n"
        "- 输出内容须与参考作品有明显差异化，若相似度>30%立即重写"
    ),
    "ip-sequel": (
        "【创作入口：IP续作 node-12 变体】\n"
        "本项目在既有 IP 世界观下创作，project_brief.ipLock 包含必须遵守的约束规则。\n"
        "核心要求：\n"
        "- ipLock.keepRules 中的每条规则均为硬约束，违反则当前节点输出作废\n"
        "- 人物性格、关键设定、世界观规则必须与原 IP 保持一致（禁止 OOC）\n"
        "- 可新增原 IP 未出现的支线角色，但核心角色行为模式不可颠覆"
    ),
    "from-outline": (
        "【创作入口：大纲扩写】\n"
        "本项目基于用户提供的分集大纲扩写，project_brief.notes 中含 [分集大纲] 原文。\n"
        "核心要求：\n"
        "- 严格遵循大纲中的集数划分与核心情节节点，不得增删集数或调换关键事件顺序\n"
        "- 扩写时补全场景、对白、情绪细节，但不改变大纲规定的故事骨架"
    ),
}


class FusionPromptBuilder:
    def __init__(self, config: FusionSkillConfig | None = None):
        self.config = config or get_fusion_config()
        self.catalog = FusionSsotCatalog(self.config)
        self._prompts = self.catalog.node_llm_prompts()
        self._registry = FusionNodeRegistry(self.config)

    def _node_meta(self, node_id: str) -> dict:
        return self._registry.node_by_fusion_id(node_id) or {}

    def build(self, node_id: str, upstream: Dict[str, Any]) -> tuple[str, str]:
        node = self._node_meta(node_id)
        schema_file = (node.get("schemaFile") or "").replace("schemas/", "")
        node_cfg = (self._prompts.get("nodes") or {}).get(node_id) or {}

        # ── System prompt ─────────────────────────────────────────────────────
        # 优先从 node-llm-prompts.json 读角色定位 + 输出指令，再交由 SkillRuleLoader 组装完整 prompt
        role = (
            node_cfg.get("role")
            or node.get("name_zh")
            or node.get("name")
            or node_id
        )
        output_instruction = (
            node_cfg.get("outputInstruction")
            or f"根据上游产物输出符合 {schema_file} 的 JSON，只输出 JSON，无 markdown 包裹。"
        )

        # DB 覆盖：如果管理后台写了完整的 system prompt，直接使用（优先级最高）
        db_system = node_cfg.get("system") or ""

        if db_system:
            system = db_system
        else:
            # 从 skill-rules JSON 文件动态组装（规则唯一来源）
            try:
                from apps.skill.skills.loader import get_skill_rule_loader
                theme = _extract_theme(upstream)
                system = get_skill_rule_loader().build_full_system_prompt(
                    node_id=node_id,
                    genre=theme,
                    role=role,
                    output_instruction=output_instruction,
                )
            except Exception as exc:
                # 兜底：退回默认格式
                import logging
                logging.getLogger(__name__).warning(
                    "[FusionPromptBuilder] SkillRuleLoader 组装失败 node=%s: %s，退回默认", node_id, exc
                )
                system = self._default_system(node, schema_file)

        # ── 多创作入口差异化 system 注入（node-11/12 FUSION-ADAPTATION.md 接入）──
        entry = _extract_creation_entry(upstream)
        entry_hint = _ENTRY_PROMPT_HINTS.get(entry, "")
        if entry_hint:
            system = f"{entry_hint}\n\n{system}"

        # ── User prompt ───────────────────────────────────────────────────────
        user_tpl = node_cfg.get("userTemplate") or (
            "请根据以下上游产物生成符合 Schema 的 JSON（只输出 JSON，无 markdown）：\n\n"
            "上游数据：\n{upstream_json}"
        )
        user = user_tpl.replace(
            "{upstream_json}",
            json.dumps(dedupe_upstream_aliases(upstream), ensure_ascii=False, indent=2),
        )
        if node_cfg.get("constraints"):
            user += "\n\n附加约束：\n" + node_cfg["constraints"]
        return system, user

    # ── 子技能 prompt ─────────────────────────────────────────────────────────
    def build_sub_skill(
        self,
        node_id: str,
        skill_id: str,
        skill_meta: Dict[str, Any],
        upstream: Dict[str, Any],
        *,
        system_hint: str = "",
    ) -> tuple[str, str]:
        node = self._node_meta(node_id)
        schema_file = (skill_meta.get("schema") or node.get("schemaFile") or "").replace("schemas/", "")
        node_cfg = (self._prompts.get("nodes") or {}).get(node_id) or {}

        parts: list[str] = []
        theme = _extract_theme(upstream)

        if system_hint:
            # system_hint 提供精确的输出字段规范（格式层），
            # 但仍需追加 Tier1 铁律 + Tier4 合规规则（质量层），二者互补不冲突
            parts.append(system_hint)
            try:
                from apps.skill.skills.loader import get_skill_rule_loader
                loader = get_skill_rule_loader()
                tier1_snippet = loader.build_tier1_node_snippet(node_id)
                if tier1_snippet:
                    parts.append(tier1_snippet)
                tier4_snippet = loader.build_tier4_snippet(node_id)
                if tier4_snippet:
                    parts.append(tier4_snippet)
            except Exception:
                pass  # 规则注入失败不影响主流程，hint 单独可用
        elif node_cfg.get("system"):
            parts.append(node_cfg["system"])
        else:
            # 完全依赖 SkillRuleLoader 组装
            try:
                from apps.skill.skills.loader import get_skill_rule_loader
                role = node_cfg.get("role") or node.get("name_zh") or node.get("name") or node_id
                output_instruction = node_cfg.get("outputInstruction") or f"输出符合 {schema_file} 的 JSON，只输出 JSON。"
                base_system = get_skill_rule_loader().build_full_system_prompt(
                    node_id=node_id,
                    genre=theme,
                    role=role,
                    output_instruction=output_instruction,
                )
                parts.append(base_system)
            except Exception:
                parts.append(self._default_system(node, schema_file))

        handbook = self.load_handbook(str(skill_meta.get("handbook") or ""))
        if handbook:
            parts.append(f"\n\n## 子技能手册（{skill_id}）\n{handbook}")

        refs = skill_meta.get("references") or []
        ref_text = self.load_reference_excerpts(refs if isinstance(refs, list) else [])
        if ref_text:
            parts.append(f"\n\n## 参考库摘要\n{ref_text}")

        desc = (skill_meta.get("description") or "").strip()
        if desc:
            parts.append(f"\n\n子技能职责：{desc}")

        # ── 多创作入口差异化注入（sub_skill 同享 node11/12 上下文）──
        entry = _extract_creation_entry(upstream)
        entry_hint = _ENTRY_PROMPT_HINTS.get(entry, "")
        if entry_hint:
            parts.insert(0, entry_hint)

        system = "\n".join(parts).strip()
        user_tpl = node_cfg.get("userTemplate") or (
            "请根据以下上游产物生成符合 Schema 的 JSON（只输出 JSON，无 markdown）：\n\n"
            "上游数据：\n{upstream_json}"
        )
        prompt_upstream = (
            pick_upstream_for_sub_skill(upstream, skill_id, skill_meta)
            if getattr(settings, "CREATION_LLM_UPSTREAM_SLIM_PROMPT", True)
            else dedupe_upstream_aliases(upstream)
        )
        user = user_tpl.replace(
            "{upstream_json}",
            json.dumps(prompt_upstream, ensure_ascii=False, indent=2),
        )
        if node_cfg.get("constraints"):
            user += "\n\n附加约束：\n" + node_cfg["constraints"]
        user += f"\n\n当前子技能：{skill_id}"
        return system, user

    # ── 工具方法 ──────────────────────────────────────────────────────────────
    def load_handbook(self, handbook_rel: str, *, max_chars: int = _HANDBOOK_MAX_CHARS) -> str:
        rel = (handbook_rel or "").strip().replace("\\", "/")
        if not rel:
            return ""
        path = self.config.root / rel
        if not path.is_file():
            return ""
        text = path.read_text(encoding="utf-8")
        return self._extract_handbook_excerpt(text, max_chars=max_chars)

    def load_reference_excerpts(
        self,
        reference_names: list,
        *,
        max_chars: int = _REFERENCE_MAX_CHARS,
    ) -> str:
        if not reference_names:
            return ""
        from apps.skill.config.portal.reference_libs import ReferenceLibraryService

        parts: list[str] = []
        budget = max_chars
        for name in reference_names:
            if not isinstance(name, str) or not name.strip():
                continue
            fname = name.strip()
            data = ReferenceLibraryService.get_json(fname)
            if not data:
                continue
            raw = json.dumps(data, ensure_ascii=False, indent=2)
            chunk = raw[: min(1200, budget)]
            if chunk:
                parts.append(f"### {fname}\n{chunk}")
                budget -= len(chunk)
            if budget <= 0:
                break
        return "\n\n".join(parts)

    @staticmethod
    def _extract_handbook_excerpt(text: str, *, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        sections: list[str] = []
        for pattern in (
            r"(## 执行步骤[\s\S]*?)(?=\n## |\Z)",
            r"(## 输出格式规范[\s\S]*?)(?=\n## |\Z)",
            r"(## 核心任务[\s\S]*?)(?=\n## |\Z)",
        ):
            match = re.search(pattern, text)
            if match:
                sections.append(match.group(1).strip())
        if sections:
            return "\n\n".join(sections)[:max_chars]
        return text[:max_chars]

    def _default_system(self, node: dict, schema_file: str) -> str:
        """兜底：规则文件不可用时的最简 system prompt。"""
        from apps.workflow.pipeline_store import FusionPipelineDbService

        schema_hint = ""
        if schema_file:
            schema_dict = FusionPipelineDbService.get_schema_dict(schema_file)
            if schema_dict:
                schema_hint = json.dumps(schema_dict, ensure_ascii=False, indent=2)[:3000]
            else:
                schema_path = self.config.schema_path(schema_file)
                if schema_path.is_file():
                    schema_hint = schema_path.read_text(encoding="utf-8")[:3000]
        return (
            f"你是短剧剧本创作流水线中的「{node.get('name', '')}」。\n"
            f"任务：{node.get('description', '')}\n"
            f"输出必须符合 JSON Schema（文件名 {schema_file}），字段名使用 camelCase。\n"
            f"禁止输出 Schema 以外的字段；禁止 markdown 包裹。\n\n"
            f"Schema 摘要：\n{schema_hint}"
        )
