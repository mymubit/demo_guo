# -*- coding: utf-8 -*-
"""
分层技能规则加载器（SkillRuleLoader）

规则唯一来源：demo4book/short-drama-script-creator/config/skill-rules/
  tier1-iron-rules.json   → 全局铁律（只读，进程级缓存）
  tier2-genre-rules.json  → 品类专属规范（可热加载）
  tier3-workflow-rules.json → 节点流程标准（可热加载）
  tier4-compliance-rules.json → 合规熔断（只读，进程级缓存）

核心接口 build_full_system_prompt(node_id, genre, role, output_instruction)
  ─ 从 JSON 文件动态组装完整 system prompt
  ─ node-llm-prompts.json 只保留角色定位 + 输出格式，规则不再写死在那里
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


# ── 路径配置 ──────────────────────────────────────────────────────────────────
def _get_rules_root() -> Path:
    """
    返回 skill-rules 目录路径。
    约定：FUSION_SKILL_ROOT 指向 demo4book/short-drama-script-creator（与 resolve_skill_root() 一致）。
    此函数只追加 config/skill-rules，不再追加 short-drama-script-creator。
    """
    raw = getattr(settings, "FUSION_SKILL_ROOT", "") or ""
    if not raw.strip():
        # 兜底：上溯到 flickplay/demo4book/short-drama-script-creator
        raw = str(Path(__file__).resolve().parents[5] / "demo4book" / "short-drama-script-creator")
    return Path(raw) / "config" / "skill-rules"


# ── 缓存层 ────────────────────────────────────────────────────────────────────
_PERMANENT_CACHE: Dict[str, Any] = {}
_HOT_RELOAD_CACHE: Dict[str, Dict[str, Any]] = {}
_HOT_RELOAD_MTIME: Dict[str, float] = {}


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[SkillRuleLoader] 加载失败 %s: %s", path, exc)
        return None


def _get_permanent(filename: str) -> Optional[Dict[str, Any]]:
    if filename not in _PERMANENT_CACHE:
        path = _get_rules_root() / filename
        if path.exists():
            data = _load_json_file(path)
            if data:
                _PERMANENT_CACHE[filename] = data
    return _PERMANENT_CACHE.get(filename)


def _get_hot_reload(filename: str) -> Optional[Dict[str, Any]]:
    path = _get_rules_root() / filename
    if not path.exists():
        return None
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    if mtime != _HOT_RELOAD_MTIME.get(filename, 0.0):
        data = _load_json_file(path)
        if data:
            _HOT_RELOAD_CACHE[filename] = data
            _HOT_RELOAD_MTIME[filename] = mtime
            logger.info("[SkillRuleLoader] 热加载规则: %s", filename)
    return _HOT_RELOAD_CACHE.get(filename)


# ── Tier1 节点级片段定义 ──────────────────────────────────────────────────────
from apps.workflow.tier1_sections import resolve_tier1_sections

# Tier1 各 section → 渲染函数（从 JSON 数据 → 可读文字）
def _render_philosophy(data: Dict[str, Any]) -> str:
    p = data.get("philosophy") or {}
    archetypes = p.get("viewer_archetypes") or []
    dqm = p.get("dream_quality_metrics") or {}
    lines = [
        "【造梦理论 · Tier1核心哲学】",
        f"核心公式：{p.get('core_formula', '')}",
        f"驱动力：{p.get('driving_force', '')}",
        "三类观众原型：",
    ]
    for a in archetypes:
        lines.append(f"  · {a.get('label','')}（{a.get('reality','')}）→ 梦境={a.get('dream','')}")
    lines += [
        "造梦三指标（必须同时达成）：",
        f"  · 绝对安全感：{dqm.get('absolute_safety','')}",
        f"  · 高效满足感：{dqm.get('efficient_satisfaction','')}",
        f"  · 强化真实感：{dqm.get('enhanced_realism','')}",
    ]
    return "\n".join(lines)


def _render_rhythm_rules(data: Dict[str, Any]) -> str:
    r = data.get("rhythm_rules") or {}
    lines = [
        "【节奏铁律 · Tier1】",
        f"  冲突升级：{r.get('conflict_escalation_interval','')}",
        f"  情绪峰值：{r.get('emotion_peak_interval','')}",
        f"  Ep3反转：{r.get('ep3_reversal','')}",
        f"  付费卡点：{r.get('ep8_10_payment_checkpoint','')}",
        f"  终极高潮：{r.get('final_climax','')}",
    ]
    return "\n".join(lines)


def _render_episode_structure(data: Dict[str, Any]) -> str:
    es = data.get("episode_structure") or {}
    tmpl = es.get("four_stage_template_90s") or {}
    lines = ["【单集四段式时间线 · Tier1（90s标准）】"]
    for seg_key, seg_label in [("0_3s","0-3s"), ("3_15s","3-15s"), ("15_75s","15-75s"), ("75_90s","75-90s")]:
        seg = tmpl.get(seg_key) or {}
        name = seg.get("name","")
        req  = seg.get("requirement","")
        lines.append(f"  {seg_label}【{name}】{req}")
        if seg.get("dialogue_max_chars"):
            lines.append(f"    台词上限：{seg['dialogue_max_chars']}字")
        if seg.get("coverage_rate"):
            lines.append(f"    覆盖率：{seg['coverage_rate']}")
        if seg.get("hook_types"):
            lines.append(f"    钩子类型：{'、'.join(seg['hook_types'])}")
        if seg.get("complete_closure") is False:
            lines.append("    禁止完整收束，必须留下集钩子")
    return "\n".join(lines)


def _render_quantitative_constraints(data: Dict[str, Any]) -> str:
    qc = data.get("quantitative_constraints") or {}
    lines = [
        "【量化硬约束 · Tier1（违反即重写）】",
        f"  钩子覆盖率：{qc.get('hook_coverage_rate','')}",
        f"  集末悬念覆盖率：{qc.get('cliffhanger_coverage_rate','')}",
        f"  场景数/集：≤{qc.get('scenes_per_episode_max',3)}个（超出比例≤{qc.get('scenes_over_limit_allowance','')}）",
        f"  台词字数正常：≤{qc.get('dialogue_chars_per_line_normal',40)}字（爆发峰值≤{qc.get('dialogue_chars_per_line_peak',50)}字）",
        f"  台词占比：≥{qc.get('dialogue_proportion_min','')}",
        f"  实质性台词（≥6字）：≥{qc.get('substantive_dialogue_min_per_episode',4)}句/集",
        f"  动作描述行：≤{qc.get('action_line_max_chars',55)}字，超限行/集≤{qc.get('action_line_over_limit_per_episode',1)}行",
        f"  字数·第1集：{qc.get('word_count_ep1',{}).get('min',900)}-{qc.get('word_count_ep1',{}).get('max',1100)}字",
        f"  字数·第2集起：{qc.get('word_count_ep2_plus',{}).get('min',700)}-{qc.get('word_count_ep2_plus',{}).get('max',900)}字（±{qc.get('word_count_tolerance',100)}字容差）",
        f"  每集反转：≥{qc.get('reversal_per_episode_min',1)}个（类型：{'、'.join(qc.get('reversal_types',[]))}）",
    ]
    return "\n".join(lines)


def _render_writing_prohibitions(data: Dict[str, Any]) -> str:
    items = data.get("writing_prohibitions") or []
    if not items:
        return ""
    lines = ["【禁止写（违反=重写，无例外）】"]
    for item in items:
        lines.append(f"  ❌ {item}")
    return "\n".join(lines)


def _render_writing_requirements(data: Dict[str, Any]) -> str:
    items = data.get("writing_requirements") or []
    if not items:
        return ""
    lines = ["【必须写】"]
    for item in items:
        lines.append(f"  ✅ {item}")
    return "\n".join(lines)


def _render_foreshadowing_rules(data: Dict[str, Any]) -> str:
    fr = data.get("foreshadowing_rules") or {}
    lines = [
        "【伏笔布局规则 · Tier1】",
        f"  小伏笔（日常小悬念）：≤{fr.get('small',{}).get('max_recovery_episodes',10)}集内回收",
        f"  大反转伏笔：大反转前≥2集埋，大反转前≥3集埋（{fr.get('major',{}).get('description','')}）",
        f"  全局伏笔回收率：{fr.get('overall_recovery_rate','≥90%')}",
    ]
    return "\n".join(lines)


def _render_qdn_model(data: Dict[str, Any]) -> str:
    qdn = data.get("qdn_emotion_model") or {}
    sc = qdn.get("shortcuts") or {}
    formulas = qdn.get("formulas") or {}
    lines = [
        "【QDN情绪化学模型 · Tier1（精准情绪工具）】",
        f"  Q=血清素（掌控感） D=多巴胺（期待感） N=去甲肾上腺素（警觉度）",
        "关键配方：",
    ]
    for key, val in formulas.items():
        if isinstance(val, dict):
            lines.append(f"  {val.get('qdn','')} = {key}（{val.get('scene','')}）")
    lines += [
        "快捷键：",
        f"  爽感·打脸 = {sc.get('catharsis','')}",
        f"  虐恋·拉扯 = {sc.get('melodrama','')}",
        f"  付费卡点 = {sc.get('payment_hook','')}",
    ]
    return "\n".join(lines)


def _render_scoring(data: Dict[str, Any]) -> str:
    sc = data.get("scoring") or {}
    grades = sc.get("grades") or {}
    dims = sc.get("dimensions") or {}
    lines = ["【评分体系 · Tier1参考】"]
    for g, v in grades.items():
        if isinstance(v, dict):
            lines.append(f"  {g}级：≥{v.get('min', v.get('max','?'))}分 - {v.get('description','')}")
    lines.append("评分维度（权重）：")
    for dim, dv in dims.items():
        if isinstance(dv, dict):
            lines.append(f"  {dim}（{dv.get('weight','')}）：{dv.get('description','')}")
    return "\n".join(lines)


def _render_format_standard(data: Dict[str, Any]) -> str:
    fs = data.get("format_standard") or {}
    lines = [
        "【格式规范 · Tier1（Variant-B行业通用版）】",
        fs.get("template", ""),
        "禁止格式：" + "；".join(fs.get("prohibitions") or []),
    ]
    return "\n".join(lines)


def _render_information_asymmetry(data: Dict[str, Any]) -> str:
    iam = data.get("information_asymmetry_mechanics") or {}
    modes = iam.get("three_modes") or []
    methods = iam.get("card_planting_methods") or []
    lines = ["【信息差三玩法 · Tier1（爽感底层机制，创作时必须主动选择）】"]
    for m in modes:
        note = f"【短剧默认】" if m.get("note") else ""
        lines.append(f"  · {m.get('mode','')}：{m.get('info_config','')} → 观众感受={m.get('audience_feeling','')} {note}")
    if methods:
        lines.append("安插信息牌四种手法：" + "、".join(f"{m.get('method','')}（{m.get('description','')}）" for m in methods))
    return "\n".join(lines)


def _render_emotion_externalization(data: Dict[str, Any]) -> str:
    eed = data.get("emotion_externalization_dict") or {}
    emotions = eed.get("emotions") or {}
    lines = ["【情绪外化词典 · Tier1（禁止心理描写，用动作替代）】"]
    labels = {"anger": "愤怒", "sadness": "悲伤", "fear": "恐惧", "surprise": "意外", "resolve": "决心"}
    for key, label in labels.items():
        e = emotions.get(key) or {}
        lines.append(
            f"  {label}：弱={e.get('weak_3_4','')} / 中={e.get('medium_6_7','')} / 强={e.get('strong_9_10','')}"
        )
    return "\n".join(lines)


def _render_ai_tone_forbidden(data: Dict[str, Any]) -> str:
    atf = data.get("ai_tone_forbidden") or {}
    phrases = atf.get("forbidden_phrases") or []
    qs = atf.get("quantitative_standard") or {}
    lines = [
        "【去AI腔规则 · Tier1（全局禁用词——全部禁止出现）】",
        "禁用词：" + "、".join(phrases),  # 全量输出，不截断
        f"量化标准：每集台词中禁用词出现≤{qs.get('max_per_episode', 1)}次",
    ]
    return "\n".join(lines)


def _render_hook_effectiveness(data: Dict[str, Any]) -> str:
    he = data.get("hook_effectiveness") or {}
    vt = he.get("validity_test") or {}
    q3 = he.get("three_core_questions") or []
    types = he.get("five_types") or []
    failures = he.get("common_failures") or []
    lines = [
        "【钩子有效性判断标准 · Tier1】",
        f"判断方法：把前5秒描述给不知道剧情的人 → {vt.get('pass','')}",
        "钩子三核心问题（至少触发一个）：" + " / ".join(q3),
        "五大钩子类型：" + "、".join(t.get("type", "") for t in types),
    ]
    if failures:
        lines.append("常见失误（禁止）：" + "；".join(f[:15] for f in failures[:3]))
    return "\n".join(lines)


def _render_episode_emotion_8nodes(data: Dict[str, Any]) -> str:
    em = data.get("episode_emotion_8nodes") or {}
    nodes = em.get("nodes") or []
    pr = em.get("episode_precision_rhythm") or {}
    lines = ["【情绪8节点模型 · Tier1（完播率+45%实测）】"]
    for n in nodes:
        lines.append(f"  {n.get('node','')}. {n.get('name','')}（{n.get('emotion_value','')}）@ {n.get('time','')}：{n.get('function','')} ")
    if pr:
        lines.append("单集精密节奏：前30s(背景+困境+动机) | 中60s(主线+关系+伏笔) | 末30s(悬念/反转)")
    return "\n".join(lines)


def _render_payment_3card(data: Dict[str, Any]) -> str:
    pc = data.get("payment_checkpoint_3card") or {}
    cards = pc.get("cards") or []
    lines = ["【付费三卡模型 · Tier1（大纲规划必须覆盖）】"]
    for c in cards:
        lines.append(f"  {c.get('card','')}（{c.get('episode_range','')}）：{c.get('recommended_content','')} ← {c.get('strategic_importance','')}")
    if pc.get("business_warning"):
        lines.append(f"  警示：{pc['business_warning'][:60]}")
    return "\n".join(lines)


def _render_dialogue_quality(data: Dict[str, Any]) -> str:
    dq = data.get("dialogue_quality") or {}
    tiers = dq.get("word_count_tiers") or []
    dims = dq.get("six_dimension_check") or []
    mono = dq.get("monologue_rules") or {}
    lines = ["【台词质量标准 · Tier1】", "字数分级："]
    for t in tiers:
        lines.append(f"  {t.get('type','')}：{t.get('chars','')} {t.get('proportion','') or t.get('note','')}")
    if dq.get("golden_ratio"):
        lines.append(f"  黄金比例：{dq['golden_ratio']}")
    lines.append("六维检查：" + " / ".join(d.get("dim", "") for d in dims))
    if mono.get("max_sentences"):
        lines.append(f"  独白规则：≤{mono['max_sentences']}句，仅用于情感爆发高光时刻")
    return "\n".join(lines)


_TIER1_RENDERERS = {
    "philosophy":                      _render_philosophy,
    "rhythm_rules":                    _render_rhythm_rules,
    "episode_structure":               _render_episode_structure,
    "quantitative_constraints":        _render_quantitative_constraints,
    "writing_prohibitions":            _render_writing_prohibitions,
    "writing_requirements":            _render_writing_requirements,
    "foreshadowing_rules":             _render_foreshadowing_rules,
    "qdn_emotion_model":               _render_qdn_model,
    "scoring":                         _render_scoring,
    "format_standard":                 _render_format_standard,
    "information_asymmetry_mechanics": _render_information_asymmetry,
    "emotion_externalization_dict":    _render_emotion_externalization,
    "ai_tone_forbidden":               _render_ai_tone_forbidden,
    "hook_effectiveness":              _render_hook_effectiveness,
    "episode_emotion_8nodes":          _render_episode_emotion_8nodes,
    "payment_checkpoint_3card":        _render_payment_3card,
    "dialogue_quality":                _render_dialogue_quality,
}


# ── 主类 ──────────────────────────────────────────────────────────────────────
class SkillRuleLoader:
    """
    分层规则加载器。

    核心接口：
      build_full_system_prompt(node_id, genre, role, output_instruction)
        → 从 JSON 文件动态组装完整 system prompt，替代 node-llm-prompts.json 里的大字符串
    """

    def get_tier1(self) -> Optional[Dict[str, Any]]:
        db_full, _ = self._db_active_content(1, "global", "", "tier_full")
        if db_full:
            return db_full
        merged = self._merge_global_sections(1)
        if merged:
            return merged
        return _get_permanent("tier1-iron-rules.json")

    def get_tier2(self) -> Optional[Dict[str, Any]]:
        db_content, _ = self._db_active_content(2, "global", "", "tier_full")
        if db_content:
            return db_content
        return _get_hot_reload("tier2-genre-rules.json")

    def get_tier3(self) -> Optional[Dict[str, Any]]:
        db_content, _ = self._db_active_content(3, "global", "", "tier_full")
        if db_content:
            return db_content
        return _get_hot_reload("tier3-workflow-rules.json")

    def get_tier4(self) -> Optional[Dict[str, Any]]:
        db_full, _ = self._db_active_content(4, "global", "", "tier_full")
        if db_full:
            return db_full
        merged = self._merge_global_sections(4)
        if merged:
            return merged
        return _get_permanent("tier4-compliance-rules.json")

    # ── Tier1 节点级片段 ───────────────────────────────────────────────────────
    def build_tier1_node_snippet(self, node_id: str) -> str:
        """按节点职责从 tier1 JSON 提取相关规则，拼成可读文本。"""
        tier1 = self.get_tier1()
        if not tier1:
            return ""
        sections = resolve_tier1_sections(node_id)
        parts = []
        for section in sections:
            renderer = _TIER1_RENDERERS.get(section)
            if renderer:
                try:
                    snippet = renderer(tier1)
                    if snippet:
                        parts.append(snippet)
                except Exception as exc:
                    logger.warning("[SkillRuleLoader] Tier1 section %s render failed: %s", section, exc)
        return "\n\n".join(parts)

    # ── DB-first 查询工具 ─────────────────────────────────────────────────────
    @staticmethod
    def _db_active_content(
        tier: int,
        scope_type: str,
        scope_key: str,
        section: str,
    ) -> Optional[Dict[str, Any]]:
        """
        查 DB 中 active 状态的规则内容。
        返回 (content_dict, rule_id) 或 (None, None)。
        优先级：DB active > JSON 文件兜底。
        """
        try:
            from apps.skill.models import SkillRuleConfig
            row = (
                SkillRuleConfig.objects.filter(
                    tier=tier,
                    scope_type=scope_type,
                    scope_key=scope_key,
                    section=section,
                    status=SkillRuleConfig.STATUS_ACTIVE,
                )
                .order_by("-updated_at")
                .first()
            )
            if row:
                return row.content, str(row.id)
        except Exception as exc:
            logger.warning("[SkillRuleLoader] DB 查询失败 tier=%s section=%s: %s", tier, section, exc)
        return None, None

    @staticmethod
    def _merge_global_sections(tier: int) -> Optional[Dict[str, Any]]:
        """将 DB 中按 section 拆分的全局规则合并为 tier JSON 结构。"""
        try:
            from apps.skill.models import SkillRuleConfig

            rows = (
                SkillRuleConfig.objects.filter(
                    tier=tier,
                    scope_type=SkillRuleConfig.SCOPE_GLOBAL,
                    scope_key="",
                    status=SkillRuleConfig.STATUS_ACTIVE,
                )
                .exclude(section__in=("tier_full", "genre_full", "pipeline_node_full"))
                .order_by("section")
            )
            merged: Dict[str, Any] = {}
            for row in rows:
                if row.section == "_meta":
                    merged["_meta"] = row.content
                else:
                    merged[row.section] = row.content
            return merged if merged else None
        except Exception as exc:
            logger.warning("[SkillRuleLoader] 合并 tier=%s section 失败: %s", tier, exc)
            return None

    # ── Tier2 品类规则（DB优先 → JSON兜底）────────────────────────────────────
    def get_genre_rules(self, genre: str) -> Optional[Dict[str, Any]]:
        """获取题材专属规则，优先从 DB 读取，DB 无 active 记录时回退到 JSON 文件。"""
        # 先查 DB（section="genre_full" 存储整个 genre 规则块）
        db_content, _ = self._db_active_content(2, "genre", genre, "genre_full")
        if db_content:
            return db_content
        return None

    def build_genre_snippet(self, genre: str, *, node_id: str = "") -> str:
        """将 Tier2 题材规则格式化为 LLM 可读片段（DB优先 + 热加载兜底）。"""
        rules = self.get_genre_rules(genre)
        if not rules:
            return ""
        label = rules.get("label", genre)
        lines = [f"【题材专属·{label}（Tier2）】"]
        # core_emotion 或 handling（mixed-theme 等使用 handling 字段）
        ce = rules.get("core_emotion") or rules.get("handling")
        if ce:
            lines.append(f"核心情绪弧/处理方式：{ce}")
        # requirements 列表
        for req in (rules.get("requirements") or []):
            lines.append(f"  · {req.get('element','')}：{req.get('standard','')}")
        # worldview_requirements dict（mixed-theme 专属字段）
        wvr = rules.get("worldview_requirements") or {}
        if isinstance(wvr, dict):
            for fname, fdesc in wvr.items():
                lines.append(f"  · 世界观/{fname}：{fdesc}")
        # dream_indicators_individual（混合题材指标）
        dii = rules.get("dream_indicators_individual")
        if dii:
            lines.append(f"  · 各题材指标下限：{dii}")
        prohibitions = rules.get("prohibitions") or []
        if prohibitions:
            lines.append("禁止：" + "；".join(prohibitions))
        compliance = rules.get("compliance_special") or []
        if compliance:
            lines.append("合规特殊：" + "；".join(compliance))
        ending = rules.get("ending_type")
        if ending:
            forbidden = rules.get("forbidden_ending", "")
            lines.append(f"结局：{ending}" + (f"（禁止：{forbidden}）" if forbidden else ""))
        note = rules.get("note")
        if note:
            lines.append(f"注：{note}")
        # 评分/放行附加条件（只对评分/质检节点注入）
        rc = rules.get("release_conditions") or {}
        if rc and node_id in ("node-6-review", "node-8-score"):
            notes = []
            if rc.get("logic_min"):
                notes.append(f"剧情逻辑维度须≥{rc['logic_min']}分")
            if rc.get("emotion_min"):
                notes.append(f"情感表达维度须≥{rc['emotion_min']}分")
            if notes:
                lines.append("放行附加条件：" + "；".join(notes) + "（即使总分≥85也须满足）")
        return "\n".join(lines)

    # ── Tier3 节点验收标准（DB优先 → JSON兜底）────────────────────────────────
    def get_node_pipeline_def(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点流程定义，优先从 DB，否则 JSON 文件（同时搜 main_pipeline + optional_nodes）。"""
        db_content, _ = self._db_active_content(3, "node", node_id, "pipeline_node_full")
        if db_content:
            return db_content
        return None

    def build_node_workflow_snippet(self, node_id: str) -> str:
        """从 Tier3 提取节点验收标准文本（DB优先 + 热加载兜底）。"""
        node_def = self.get_node_pipeline_def(node_id)
        if not node_def:
            return ""
        parts: List[str] = []

        # ── validation.gate_conditions（node-1 立项验收，嵌套在 validation 内）
        val = node_def.get("validation") or {}
        val_gc = val.get("gate_conditions") or []
        if val_gc:
            rows = ["【立项验收条件（Tier3·node-1）】"]
            rows += [f"  ✓ {c}" for c in val_gc]
            if val.get("pre_compliance"):
                rows.append(f"  前置：{val['pre_compliance']}")
            parts.append("\n".join(rows))

        # ── six_stage_structure（node-2 六阶段宏观架构）──────────────────────
        # 数据结构：{"description": "...", "stages": [{stage, name, ratio, function, emotion_range}]}
        sss_raw = node_def.get("six_stage_structure") or {}
        sss = sss_raw.get("stages", []) if isinstance(sss_raw, dict) else (sss_raw if isinstance(sss_raw, list) else [])
        if sss:
            rows = ["【六阶段宏观架构（Tier3·node-2，标准100集）】"]
            for s in sss:
                if not isinstance(s, dict):
                    continue
                rows.append(
                    f"  阶段{s.get('stage','')}({s.get('name','')} {s.get('ratio', s.get('proportion',''))})："
                    f"情绪{s.get('emotion_range','')} → {s.get('function','')}"
                )
            parts.append("\n".join(rows))

        # ── worldview_required_fields（node-2 世界观必填）────────────────────
        # 数据格式可能是 list[{field,description,min}] 或 dict{fieldName: {description,min_count}}
        wvrf_raw = node_def.get("worldview_required_fields")
        if wvrf_raw:
            rows = ["【世界观块必填字段（Tier3·node-2）】"]
            if isinstance(wvrf_raw, list):
                for f in wvrf_raw:
                    if isinstance(f, dict):
                        rows.append(f"  · {f.get('field','')}：{f.get('description','')}（最低：{f.get('min','')}）")
            elif isinstance(wvrf_raw, dict):
                for fname, fmeta in wvrf_raw.items():
                    if isinstance(fmeta, dict):
                        min_v = fmeta.get("min_count") or fmeta.get("min") or ""
                        rows.append(f"  · {fname}：{fmeta.get('description','')}（最低：{min_v}）")
                    else:
                        rows.append(f"  · {fname}：必填")
            parts.append("\n".join(rows))

        # ── reversal_position_table（node-2 反转位置分配）────────────────────
        rpt = node_def.get("reversal_position_table") or []
        if rpt:
            rows = ["【反转位置分配规则（Tier3·node-2）】"]
            for r in rpt:
                rows.append(
                    f"  {r.get('type','')} @ {r.get('episode_range','')}：{r.get('foreshadow_requirement','')}"
                )
            parts.append("\n".join(rows))

        # ── gate_rules.checks（node-5 逐集门禁代码列表）──────────────────────
        gate_rules = node_def.get("gate_rules") or {}
        if gate_rules.get("checks"):
            parts.append(
                "【逐集Gate门禁（Tier3）】\n"
                + "\n".join(f"  ✓ {c}" for c in gate_rules["checks"])
            )

        # ── gate_check_detail（node-5 人类可读详细版）────────────────────────
        gcd = node_def.get("gate_check_detail") or []
        if gcd:
            rows = ["【逐集Gate详细标准（Tier3）】"]
            for item in gcd:
                rows.append(
                    f"  {item.get('check','')}：{item.get('standard','')} → 失败={item.get('fail_action','重写')}"
                )
            if node_def.get("writing_rule"):
                rows.append(f"  写作铁律：{node_def['writing_rule']}")
            parts.append("\n".join(rows))

        # ── episode_time_quota（node-5 字数配额）─────────────────────────────
        etq = node_def.get("episode_time_quota") or {}
        if etq:
            rows = [f"【单集字数配额（Tier3·{etq.get('description','')}）】"]
            for seg, info in etq.items():
                if seg == "description" or not isinstance(info, dict):
                    continue
                rows.append(f"  {seg}【{info.get('name','')}】：{info.get('chars','')}字")
            parts.append("\n".join(rows))

        # ── gate_conditions（node-6 质检放行条件）────────────────────────────
        gc = node_def.get("gate_conditions") or []
        if gc:
            rows = ["【质检放行条件（Tier3·node-6）】"]
            rows += [f"  ✓ {c}" for c in gc]
            if node_def.get("pass_action"):
                rows.append(f"  通过→ {node_def['pass_action']}")
            if node_def.get("fail_action"):
                rows.append(f"  失败→ {node_def['fail_action']}")
            rows.append(f"  最大修复轮数：{node_def.get('max_fix_rounds', 2)}轮")
            parts.append("\n".join(rows))

        # ── quick_scoring_4dim（node-6 四维快评）─────────────────────────────
        qs4 = node_def.get("quick_scoring_4dim") or {}
        dims4 = qs4.get("dimensions") or []
        if dims4:
            rows = ["【四维快评（Tier3·node-6）】"]
            for d in dims4:
                rows.append(f"  {d.get('name','')}({d.get('weight','')})：{d.get('covers','')}")
            parts.append("\n".join(rows))

        # ── deep_scoring_8dim（node-8 八维深度评分）──────────────────────────
        ds8 = node_def.get("deep_scoring_8dim") or {}
        dims8 = ds8.get("dimensions") or []
        if dims8:
            rows = ["【八维深度评分（Tier3·node-8）】"]
            for d in dims8:
                rows.append(
                    f"  {d.get('name','')} {int(d.get('weight', 0) * 100)}%：{d.get('description','')}"
                )
            parts.append("\n".join(rows))

        # ── node-8 report_format + release_conditions ─────────────────────
        rf = node_def.get("report_format") or {}
        if rf.get("required_fields"):
            parts.append(
                "【评分报告必须包含（Tier3）】\n"
                + "\n".join(f"  · {f}" for f in rf["required_fields"])
            )
        rc8 = node_def.get("release_conditions") or {}
        if rc8:
            rows = ["【放行判断规则（Tier3·node-8）】"]
            for track, cond in rc8.items():
                if isinstance(cond, dict):
                    rows.append(
                        f"  {track}：总分≥{cond.get('min_total',85)}，各维度≥{cond.get('min_dimension',75)}"
                    )
                elif isinstance(cond, str):
                    rows.append(f"  {track}：{cond}")
            parts.append("\n".join(rows))

        # ── character_archetypes（node-3 原型库）──────────────────────────
        archetypes = node_def.get("character_archetypes") or []
        if archetypes:
            rows = ["【角色原型库（Tier3·node-3，选择适配题材原型）】"]
            for a in archetypes:
                fit_str = "/".join(a.get("fit", []))
                rows.append(f"  {a.get('archetype','')}：{a.get('core','')}（适配：{fit_str}）")
            parts.append("\n".join(rows))

        # ── character_bible_required_fields（node-3 角色圣经必填字段）─────
        cbrf = node_def.get("character_bible_required_fields") or []
        if cbrf:
            rows = ["【人设圣经必填字段（Tier3·node-3）】"]
            for f in cbrf:
                rows.append(f"  · {f.get('field','')}：{f.get('description','')}")
            parts.append("\n".join(rows))

        # ── antagonist_rules（node-3 反派设定）────────────────────────────
        antr = node_def.get("antagonist_rules") or []
        if antr:
            parts.append("【反派设定规则（Tier3·node-3）】\n" + "\n".join(f"  · {r}" for r in antr))

        # ── per_episode_required_fields（node-4 大纲逐集必填）────────────
        perf = node_def.get("per_episode_required_fields") or []
        if perf:
            rows = ["【大纲每集必填字段（Tier3·node-4）】"]
            for f in perf:
                vals = "、".join(str(v) for v in (f.get("values") or []))
                rows.append(
                    f"  · {f.get('field','')}：{f.get('description','')}"
                    + (f"  取值：{vals}" if vals else "")
                )
            parts.append("\n".join(rows))

        # ── function_tags_11（node-4 功能标签）────────────────────────────
        ft11 = node_def.get("function_tags_11") or {}
        tags = ft11.get("tags") or []
        if tags:
            mandatory = ft11.get("mandatory_per_episode") or []
            rows = [
                f"【11种功能标签（Tier3·node-4，全剧每种≥3次）】",
                "  每集必须包含：" + "、".join(mandatory),
            ]
            tag_names = " / ".join(t.get("tag", "") for t in tags)
            rows.append("  所有标签：" + tag_names)
            parts.append("\n".join(rows))

        # ── reversal_codes_21（node-4 反转代码速查）──────────────────────
        rc21 = node_def.get("reversal_codes_21") or {}
        codes = rc21.get("codes") or []
        if codes:
            rows = ["【21种反转代码速查（Tier3·node-4，reversalCode字段取值）】"]
            for c in codes:
                rows.append(
                    f"  {c.get('code','')} {c.get('name','')}（{c.get('type','')}）→ {c.get('timing','')}"
                )
            checklist = rc21.get("quality_checklist") or []
            if checklist:
                rows.append("  每个反转须满足：" + "；".join(checklist[:2]))
            anti = rc21.get("anti_patterns") or []
            if anti:
                rows.append("  反模式禁止：" + "；".join(anti[:3]))
            parts.append("\n".join(rows))

        # ── quality_gates（通用）──────────────────────────────────────────
        qg = node_def.get("quality_gates") or {}
        if qg:
            rows = ["【节点质量门禁（Tier3）】"]
            for k, v in qg.items():
                rows.append(f"  {k}: {v}")
            parts.append("\n".join(rows))

        return "\n\n".join(parts)

    # ── 调用链追踪：返回本次生成使用的 rule_config_ids ──────────────────────
    def collect_used_rule_ids(self, node_id: str, genre: Optional[str] = None) -> Dict[str, str]:
        """
        返回本次 build_full_system_prompt 中实际使用的 DB rule config ID 映射。
        供 persist_execution_trace 记录调用链。
        格式：{ "tier2_genre": "<uuid>", "tier3_node": "<uuid>" }
        """
        ids: Dict[str, str] = {}
        if genre:
            _, rule_id = self._db_active_content(2, "genre", genre, "genre_full")
            if rule_id:
                ids["tier2_genre"] = rule_id
        _, rule_id = self._db_active_content(3, "node", node_id, "pipeline_node_full")
        if rule_id:
            ids["tier3_node"] = rule_id
        return ids

    # ── Tier4 核心合规片段（按节点选择性注入）────────────────────────────────
    def build_tier4_snippet(self, node_id: str) -> str:
        """
        从 Tier4 提取与节点职责相关的合规约束。
        - node-1-input: P0 熔断红线列表（立项时题材级检测警示）
        - node-5-script: 价值观兜底 + AI腔禁用标准 + 正义收束规则
        - node-6-review / node-8-score: 九维评估摘要
        """
        tier4 = self.get_tier4()
        if not tier4:
            return ""
        lines: List[str] = []

        if node_id == "node-1-input":
            # P0 红线提示
            p0 = tier4.get("p0_categories") or []
            lines.append("【合规红线 · Tier4·P0（题材立项检查，以下任一触发即熔断）】")
            for cat in p0[:6]:  # 取前6条最关键的
                patterns_preview = "、".join((cat.get("patterns") or [])[:3])
                lines.append(f"  ❌ {cat.get('label','')}：{patterns_preview}...")

        elif node_id == "node-5-script":
            # 价值观兜底
            vbl = tier4.get("values_bottom_line") or {}
            pv = vbl.get("prohibited_values") or []
            if pv:
                lines.append("【价值观兜底 · Tier4（触发即强制修改）】")
                for v in pv:
                    lines.append(f"  ❌ {v.get('label','')}：{v.get('description','')}")
            # 正义收束
            jtr = tier4.get("justice_tail_rule") or {}
            if jtr:
                lines.append(f"【正义收束规则 · Tier4】{jtr.get('mandatory_for_all','')}")
                qt = jtr.get("quantitative_triggers") or {}
                if qt.get("crime_markers_2_4"):
                    lines.append(f"  犯罪词2-4次：{qt['crime_markers_2_4'].get('requirement','')}")
                if qt.get("crime_markers_5plus"):
                    lines.append(f"  犯罪词≥5次：{qt['crime_markers_5plus'].get('requirement','')}")

        elif node_id == "node-3-character":
            # 人设阶段：禁止塑造宣扬违禁价值观的人物
            vbl = tier4.get("values_bottom_line") or {}
            pv = vbl.get("prohibited_values") or []
            if pv:
                lines.append("【人设价值观兜底 · Tier4（人物塑造必须满足）】")
                for v in pv[:4]:
                    lines.append(f"  ❌ {v.get('label','')}：{v.get('description','')}")
            jtr = tier4.get("justice_tail_rule") or {}
            if jtr:
                lines.append(f"  人设铁律：反派须有正义收束结局——{jtr.get('mandatory_for_all','')}")

        elif node_id == "node-2-structure":
            # 世界观/设定级 P1 合规要求（设定选型时须预置正义收束）
            p1 = tier4.get("p1_categories") or []
            jtr = tier4.get("justice_tail_rule") or {}
            if p1 or jtr:
                lines.append("【设定级合规要求 · Tier4·P1（世界观选型必看）】")
                for cat in p1[:5]:  # 取前5条最相关的设定类风险
                    action = cat.get("action", "")
                    lines.append(f"  ⚠️ {cat.get('label','')}：{action}")
                if jtr:
                    lines.append(f"  正义收束铁律：{jtr.get('mandatory_for_all','')}")

        elif node_id == "node-4-outline":
            # 大纲规划阶段：价值观兜底
            vbl = tier4.get("values_bottom_line") or {}
            pv = vbl.get("prohibited_values") or []
            if pv:
                lines.append("【价值观兜底 · Tier4（大纲阶段确认情节不违禁）】")
                for v in pv[:5]:
                    lines.append(f"  ❌ {v.get('label','')}：{v.get('description','')}")
            jtr = tier4.get("justice_tail_rule") or {}
            if jtr:
                lines.append(f"  正义收束要求：{jtr.get('mandatory_for_all','')}")

        elif node_id in ("node-6-review", "node-8-score"):
            # 九维评估概要
            ndr = tier4.get("nine_dimension_risk_assessment") or {}
            dims = ndr.get("dimensions") or []
            if dims:
                lines.append("【九维过审风险评估 · Tier4】")
                for d in dims:
                    veto = d.get("veto_threshold", 8)
                    low = "（低门槛）" if d.get("note") == "低门槛" else ""
                    lines.append(f"  {d.get('name','')}：单项否决线≥{veto}{low}")
                oj = ndr.get("overall_judgment") or {}
                hr = oj.get("high_risk") or {}
                lines.append(f"  高风险触发：{hr.get('condition','')}")

        elif node_id == "node-7-polish":
            # 润色阶段：禁止在润色中引入违禁内容
            vbl = tier4.get("values_bottom_line") or {}
            pv = vbl.get("prohibited_values") or []
            if pv:
                lines.append("【润色合规兜底 · Tier4（润色不得引入违禁内容）】")
                for v in pv[:3]:
                    lines.append(f"  ❌ {v.get('label','')}：{v.get('description','')}")
            jtr = tier4.get("justice_tail_rule") or {}
            if jtr:
                lines.append(f"  正义收束铁律：{jtr.get('mandatory_for_all','')}")

        elif node_id == "node-10-insight":
            # 内容洞察：原创性规则（洞察结果不得直接复制参考作品）
            orig = tier4.get("originality_rules") or {}
            thresholds = orig.get("thresholds") or {}
            if thresholds:
                lines.append("【原创性合规要求 · Tier4（洞察萃取须满足）】")
                for k, v in list(thresholds.items())[:4]:
                    lines.append(f"  · {k}：≤{v}")
            prohibition = orig.get("prohibition") or orig.get("general_prohibition")
            if prohibition:
                lines.append(f"  禁止：{prohibition}")

        elif node_id == "node-9-adapt":
            # 平台改编：平台量化合规要求
            pq = tier4.get("shortdramas_platform_quantitative") or {}
            if pq:
                lines.append("【平台改编合规要求 · Tier4】")
                for platform, rules in pq.items():
                    if isinstance(rules, dict):
                        req = "; ".join(f"{k}={v}" for k, v in rules.items() if not isinstance(v, dict))
                        if req:
                            lines.append(f"  {platform}：{req}")

        elif node_id == "node-11-marketing":
            # 营销文案：片名/宣传合规
            tcr = tier4.get("title_compliance_rules") or {}
            if tcr:
                lines.append("【片名/宣传合规规则 · Tier4】")
                prohibitions = tcr.get("prohibited_elements") or []
                for p in prohibitions[:5]:
                    lines.append(f"  ❌ {p}")
                naming = tcr.get("naming_requirements") or []
                for r in naming[:3]:
                    lines.append(f"  ✓ {r}")

        return "\n".join(lines)

    # ── 核心接口：完整 system prompt 组装 ─────────────────────────────────────
    def build_full_system_prompt(
        self,
        node_id: str,
        genre: Optional[str],
        role: str,
        output_instruction: str,
    ) -> str:
        """
        从 tier JSON 文件动态组装完整 system prompt。

        组装顺序（总典四层优先级）：
          [角色定位]  → role + output_instruction（来自 node-llm-prompts.json 的极简配置）
          [Tier1]     → 按节点职责提取的全局铁律片段
          [Tier2]     → 品类专属规则（按 genre 热加载）
          [Tier3]     → 节点验收标准（按 node_id 热加载）
          [Tier4]     → 核心合规约束（按节点选择性注入）
        """
        parts: List[str] = []

        # 1. 角色定位 + 输出指令
        parts.append(f"你是{role}（中文商业化短剧平台专用）。\n\n【输出】{output_instruction}")

        # 2. Tier1 全局铁律（按节点最小化提取）
        tier1_snippet = self.build_tier1_node_snippet(node_id)
        if tier1_snippet:
            parts.append(tier1_snippet)

        # 3. Tier2 品类专属规则（热加载，评分节点额外注入 release_conditions）
        if genre:
            genre_snippet = self.build_genre_snippet(genre, node_id=node_id)
            if genre_snippet:
                parts.append(genre_snippet)

        # 4. Tier3 节点验收标准（热加载）
        workflow_snippet = self.build_node_workflow_snippet(node_id)
        if workflow_snippet:
            parts.append(workflow_snippet)

        # 5. Tier4 核心合规约束（选择性注入，不给所有节点注入，避免 token 浪费）
        tier4_snippet = self.build_tier4_snippet(node_id)
        if tier4_snippet:
            parts.append(tier4_snippet)

        return "\n\n".join(parts)

    # ── 兼容旧接口（prompt_builder.py 追加模式，逐步废弃）─────────────────────
    def build_system_injection(self, node_id: str, genre: Optional[str] = None) -> str:
        """
        旧接口：仅返回 Tier2+Tier3 追加片段（不包含 Tier1）。
        新代码应使用 build_full_system_prompt()。
        """
        parts = []
        if genre:
            g = self.build_genre_snippet(genre)
            if g:
                parts.append(g)
        w = self.build_node_workflow_snippet(node_id)
        if w:
            parts.append(w)
        return "\n\n".join(parts)


# 模块级单例
_loader_instance: Optional[SkillRuleLoader] = None


def get_skill_rule_loader() -> SkillRuleLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = SkillRuleLoader()
    return _loader_instance
