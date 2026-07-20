# -*- coding: utf-8 -*-
"""按角色契约组装 LLM 提示词，不泄露无关角色 prompt。

渐进披露：
- L0 角色边界 + SKILL 索引体
- L1 按需 modules（enable_when；默认全文，不做预算截断）
- L2 rules（sections 收窄；默认全文）
- L3 输出契约 + 反例 + 知识引用（默认全文）
"""
from __future__ import annotations

import json
from typing import Any

from apps.drama.services.injection_manifest import build_injection_manifest, layer_stat
from apps.drama.services.schema_prompt_contract import (
    extract_required_paths,
    load_artifact_fixture,
    render_contract_block,
)
from apps.drama.services.skills_loader import SkillsBundleLoader, get_skills_loader
from django.conf import settings as django_settings


def _effective_max_chars(raw: int) -> int:
    """SKILLS_INJECTION_POLICY_ENFORCED=false 时忽略预算（逃生阀）。"""
    if raw <= 0:
        return 0
    if not getattr(django_settings, "SKILLS_INJECTION_POLICY_ENFORCED", True):
        return 0
    return int(raw)


class PromptBuilder:
    """基于 Skills SSOT 构建 system/user prompt。"""

    def __init__(self, loader: SkillsBundleLoader | None = None) -> None:
        self.loader = loader or get_skills_loader()

    def build(
        self,
        role: str,
        *,
        settings: dict[str, Any],
        workflow_state: dict[str, Any],
        artifacts: dict[str, Any],
        input_payload: dict[str, Any] | None = None,
        latest_script: dict[str, Any] | None = None,
        scoring_mode: str = "project",
    ) -> tuple[str, str, dict[str, Any]]:
        contract = self.loader.get_role_contract(role)
        entry = self.loader.get_role_entry(role)
        # rule_policy.max_chars：缺省 0=不截断；仅显式正数且 ENFORCED 时启用预算
        rule_policy = contract.get("rule_policy") or {}
        max_chars = _effective_max_chars(int(rule_policy.get("max_chars") or 0))
        knowledge_policy = contract.get("knowledge_policy") or {}
        knowledge_budget = _effective_max_chars(
            int(knowledge_policy.get("max_chars") or 0)
        )
        knowledge_mode = str(knowledge_policy.get("mode") or "full").strip().lower()
        module_policy = contract.get("module_policy") or {}
        module_as_index = bool(module_policy.get("as_index"))
        module_budget = _effective_max_chars(int(module_policy.get("max_chars") or 0))

        skill_text = self.loader.load_skill(role)
        modules_asm = self.loader.assemble_modules_for_role(
            role,
            settings,
            as_index=module_as_index,
            budget_max_chars=module_budget,
        )
        rules_asm = self.loader.assemble_rules_for_role(
            role, settings, max_chars=max_chars
        )
        anti_text = self.loader.load_anti_examples(role)
        # mode=index：按模块索引风格只注文件名+首行；sections 暂与 full 同路径，靠 max_chars 护栏
        knowledge_as_index = knowledge_mode == "index"
        knowledge_asm = self.loader.assemble_knowledge_for_role(
            role,
            settings,
            max_chars=knowledge_budget,
            as_index=knowledge_as_index,
        )
        fewshot_text = self.loader.load_fewshots(role)
        modules_text = modules_asm["text"]
        rules_text = rules_asm["text"]
        knowledge_text = knowledge_asm["text"]
        runtime = self.loader.project_runtime_projection(role, settings, workflow_state)
        artifact_key = self.loader.get_output_artifact_by_role(role)
        schema_version = self.loader.artifact_schema_version(artifact_key)
        artifact_schema = _safe_load_artifact_schema(self.loader, artifact_key)
        artifact_fixture = (
            load_artifact_fixture(self.loader, artifact_key)
            if artifact_schema is not None
            else None
        )
        contract_block = (
            render_contract_block(
                artifact_key,
                artifact_schema,
                fixture=artifact_fixture,
                max_chars=3500,
            )
            if artifact_schema is not None
            else ""
        )
        schema_required_paths = (
            extract_required_paths(artifact_schema) if artifact_schema is not None else []
        )
        scoring_inline = (
            _inline_quality_scoring(self.loader, settings)
            if role == "drama.script-scorer"
            else ""
        )

        header_lines = [
            f"你是 {entry.get('name_zh', role)}（agent_id={role}）。",
            contract.get("role", ""),
        ]
        header_text = "\n".join(header_lines)

        system_parts = [
            *header_lines,
            "",
            "## 职责与技能",
            skill_text,
        ]
        if modules_text:
            system_parts.extend(["", "## 模块步骤", modules_text])
        if scoring_inline:
            system_parts.extend(["", scoring_inline])
        if rules_text:
            system_parts.extend(["", "## 规则与约束", rules_text])
        if knowledge_text:
            system_parts.extend(["", "## 参考知识（节选）", knowledge_text])
        if fewshot_text:
            system_parts.extend(["", "## Few-shot 示例", fewshot_text])
        if anti_text:
            system_parts.extend(["", "## 输出反例（禁止复现）", anti_text])
        contract_header_parts = [
            "",
            "## 输出契约",
            f"- artifact_key: {artifact_key}",
            f"- schema_version: {schema_version}",
            "仅输出符合 schema 的 JSON 对象，不要输出解释文字，不要包裹 markdown 代码围栏。",
            *_output_schema_hints(artifact_key, self.loader),
        ]
        system_parts.extend(contract_header_parts)
        if contract_block:
            system_parts.extend(["", contract_block])
        system_prompt = "\n".join(part for part in system_parts if part is not None)

        user_body: dict[str, Any] = {
            "runtime_projection": runtime,
            "project_settings": _settings_subset(settings),
            "input": input_payload or {},
            "required_artifacts": _required_artifacts(contract, artifacts),
            "output": {
                "artifact_key": artifact_key,
                "schema_version": schema_version,
                "schema_required_paths": schema_required_paths,
            },
        }
        if latest_script is not None:
            user_body["latest_script"] = latest_script
        if scoring_mode:
            user_body["scoring_mode"] = scoring_mode

        user_prompt = json.dumps(user_body, ensure_ascii=False, indent=2)

        # contract 层 = 输出契约标题块 + 可选 skeleton（不含前面各层）
        contract_layer_text = "\n".join(
            part for part in [*contract_header_parts, *(["", contract_block] if contract_block else [])]
            if part is not None
        )

        layers = {
            "header": layer_stat(len(header_text)),
            "skill": layer_stat(len(skill_text)),
            "modules": layer_stat(
                len(modules_text), truncated=bool(modules_asm.get("truncated"))
            ),
            "rules": layer_stat(
                len(rules_text), truncated=bool(rules_asm.get("truncated"))
            ),
            "knowledge": layer_stat(
                len(knowledge_text), truncated=bool(knowledge_asm.get("truncated"))
            ),
            "fewshots": layer_stat(len(fewshot_text)),
            "anti": layer_stat(len(anti_text)),
            "scoring_inline": layer_stat(len(scoring_inline)),
            "contract": layer_stat(len(contract_layer_text)),
        }
        manifest = build_injection_manifest(
            agent_id=role,
            bundle_version=self.loader.bundle_version,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            layers=layers,
            modules={
                "included": list(modules_asm.get("included") or []),
                "skipped": list(modules_asm.get("skipped") or []),
            },
            knowledge={
                "included": list(knowledge_asm.get("included") or []),
                "skipped": list(knowledge_asm.get("skipped") or []),
            },
            rules={
                "sections_included": list(rules_asm.get("sections_included") or []),
                "item_count": int(rules_asm.get("item_count") or 0),
                "truncated": bool(rules_asm.get("truncated")),
                "max_chars": int(rules_asm.get("max_chars") or 0),
            },
            policies={
                "evaluate_enable_when": bool(
                    modules_asm.get("evaluate_enable_when")
                ),
                "module_max_chars": int(modules_asm.get("max_chars") or 0),
                "rule_max_chars": max_chars,
                "knowledge_max_chars": knowledge_budget,
                "module_as_index": module_as_index,
                "knowledge_mode": knowledge_mode,
                "policy_enforced": bool(
                    getattr(django_settings, "SKILLS_INJECTION_POLICY_ENFORCED", True)
                ),
            },
        )
        return system_prompt, user_prompt, manifest


def _settings_subset(settings: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "entry_type",
        "title",
        "core_idea",
        "synopsis",
        "external_story",
        "adapt_notes",
        "genre_matrix",
        "audience_channel",
        "protagonist_structure",
        "flavor_tags",
        "episode_count",
        "target_platform",
        "creation_preferences",
        "production_context",
        "derived",
    )
    return {key: settings[key] for key in keys if key in settings}


def _safe_load_artifact_schema(
    loader: SkillsBundleLoader, artifact_key: str
) -> dict[str, Any] | None:
    try:
        return loader.load_artifact_schema(artifact_key)
    except Exception:
        return None


def _output_schema_hints(artifact_key: str, loader: SkillsBundleLoader) -> list[str]:
    """仅保留 schema 外的行为约束；必填字段由契约块统一提供，避免重复。"""
    hints: list[str] = []
    if artifact_key == "project_brief":
        hints.extend(
            [
                "- genre_matrix 必须包含 emotion/identity/conflict/world/audience_channel；"
                "protagonist_structure、flavor_tags 放在 genre_matrix 内。",
                "- 不要输出 rule_params（由系统按题材矩阵合成）；blockbuster_factors 必须是字符串数组；"
                "compliance_risk 只能是 low|medium|high。",
                "- 不要输出 artifact_key、schema_version、sensitivity_pre_check 等 schema 外字段。",
            ]
        )
    if artifact_key == "story_bible":
        hints.extend(
            [
                "- synopsis 必须是对象，且同时包含 short（短梗概）与 full（完整梗概），"
                "不要把 synopsis 写成字符串。",
                "- adapt_source.mode 只能是 original 或 adapt；"
                "characters[].role_type 只能是 protagonist|antagonist|supporting。",
                "- series_structure.six_stage_structure 必须恰好 6 项；"
                "不要输出 schema 外字段。",
            ]
        )
    if artifact_key == "quality_report":
        hints.extend(
            [
                "- dimensions 必须是对象，键为 format/narrative/conflict/character/"
                "emotion/logic/satisfaction/hooks/paywall/genre_fit。",
                "- 每个维度必须含 score、weight、evidence、deductions；"
                "evidence 必须为非空字符串数组，须引用具体集数/场景/台词；"
                "禁止空数组、禁止只输出分数。",
                "- 【篇幅硬要求】每个维度分析正文（evidence 各条拼接，可计入 deductions）"
                "约 1000 字、不得少于 800 字；写清优点/问题/证据，禁止一句话糊弄。",
                "- 【篇幅硬要求】另写 verdict_detail 总评约 2000 字、不得少于 1500 字；"
                "覆盖整体强弱、关键缺陷、返修优先级与可否进下一批的理由。"
                "continuity_summary.summary 建议不少于 300 字。",
                "- deductions 写扣分与代价；先写 evidence，再打 0-100 分。",
                "- needs_revision=false 时 verdict 不得为「重大返工」。"
                "verdict 仍用枚举（通过/条件通过/需要修改/重大返工），长文放 verdict_detail。",
            ]
        )
    if artifact_key == "compliance_report":
        hints.extend(
            [
                "- blocking_issues 与 risk_items 须写明具体违规点、涉及集数/场景与修改建议，"
                "禁止仅输出类别名或模板化空话。",
                "- risk_items[].type 只能是 p0|p1|p2。",
            ]
        )
    return hints


def _inline_quality_scoring(
    loader: SkillsBundleLoader,
    settings: dict[str, Any],
) -> str:
    """把 quality-scoring.yaml + 当前 preset 权重内联进评分官 prompt。"""
    try:
        scoring = loader.load_seed_yaml("foundation/constraints/quality-scoring.yaml")
        presets = loader.load_seed_yaml("foundation/constraints/scoring-presets.yaml")
    except FileNotFoundError:
        return ""

    prefs = settings.get("creation_preferences") or {}
    preset_id = str(prefs.get("scoring_preset") or "standard")
    preset_map = presets.get("presets") if isinstance(presets.get("presets"), dict) else {}
    if preset_id not in preset_map:
        preset_id = "standard"
    preset = preset_map.get(preset_id) or {}
    weights = preset.get("weights") if isinstance(preset.get("weights"), dict) else {}
    pass_threshold = preset.get("pass_threshold", scoring.get("revision_threshold", 75))

    lines = [
        "## 评分细则（内联）",
        f"- scoring_preset={preset_id}",
        f"- pass_threshold={pass_threshold}",
        f"- revision_threshold={scoring.get('revision_threshold')}",
        f"- evolution_threshold={scoring.get('evolution_threshold')}",
        f"- grade_thresholds={json.dumps(scoring.get('grade_thresholds') or {}, ensure_ascii=False)}",
        "- 十维定义与权重（先证据后打分；每维必须输出 evidence[] 与 deductions[]）：",
    ]
    length = scoring.get("output_length") if isinstance(scoring.get("output_length"), dict) else {}
    if length:
        lines.extend(
            [
                "## 篇幅硬要求（基础量，少则说不清）",
                f"- 每维分析约 {length.get('dimension_analysis_target_chars', 1000)} 字"
                f"（evidence+deductions 合计，下限 {length.get('dimension_analysis_min_chars', 800)} 字）",
                f"- verdict_detail 总评约 {length.get('verdict_detail_target_chars', 2000)} 字"
                f"（下限 {length.get('verdict_detail_min_chars', 1500)} 字）",
                f"- continuity_summary.summary 建议不少于"
                f" {length.get('continuity_summary_min_chars', 300)} 字",
                "- 禁止「分数+一句话」空壳报告；宁可多写具体集数/场景/台词引用。",
            ]
        )
    for dim in scoring.get("dimensions") or []:
        if not isinstance(dim, dict):
            continue
        key = str(dim.get("key") or "")
        if not key:
            continue
        weight = weights.get(key, dim.get("weight"))
        name = dim.get("name") or key
        desc = str(dim.get("desc") or "").strip()
        lines.append(f"  - {key}（{name}）weight={weight}: {desc}")
    return "\n".join(lines)


def _required_artifacts(
    contract: dict[str, Any],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    input_contract = contract.get("input_contract") or {}
    required = list(input_contract.get("required_artifacts") or [])
    optional = list(input_contract.get("optional_artifacts") or [])
    keys = list(dict.fromkeys([*required, *optional]))
    result: dict[str, Any] = {}
    for key in keys:
        if key == "latest_script":
            continue
        if key in artifacts:
            result[key] = _compact_artifact_payload(key, artifacts[key])
    return result


def _compact_artifact_payload(artifact_key: str, payload: Any) -> Any:
    """压缩上游产物，降低蓝图等长调用的提示词体积与首包等待。"""
    if not isinstance(payload, dict):
        return payload
    if artifact_key != "project_brief":
        return payload

    keep_keys = (
        "title",
        "core_idea",
        "genre_matrix",
        "target_audience",
        "core_conflict",
        "hook_concept",
        "commercial_hook",
        "episode_count",
        "compliance_risk",
        "first_episode_hook",
        "paywall_direction",
        "market_opportunity",
        "differentiation_strategy",
        "blockbuster_factors",
    )
    compact: dict[str, Any] = {}
    for key in keep_keys:
        if key not in payload:
            continue
        value = payload[key]
        if isinstance(value, str) and len(value) > 400:
            compact[key] = f"{value[:400]}…"
        elif key == "blockbuster_factors" and isinstance(value, list):
            compact[key] = value[:5]
        elif key == "competitor_references" and isinstance(value, list):
            compact[key] = value[:2]
        else:
            compact[key] = value
    return compact
