# -*- coding: utf-8 -*-
"""LearnedRulesRecorder：跨项目经验沉淀。

来自 Novel-to-Script-Team knowledge-curator 设计理念：
  - 当 ConvergenceService 触发停机时，分析失败模式
  - 若同类失败在多个项目中重复出现（≥ 阈值），自动沉淀为规则
  - 写入 ai-drama-skills-v2/knowledge/learned-rules.md
  - 供后续 ReviewAgent / ScriptAgent 参考，形成系统性经验闭环
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 学习规则文件路径（相对于 ScriptForge/backend）
_LEARNED_RULES_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "ai-drama-skills-v2", "knowledge", "learned-rules.md",
))

# 失败模式出现次数达到此阈值才沉淀规则
_PATTERN_THRESHOLD = 3

# 经验条目记录文件（JSON，供统计分析）
_PATTERN_LOG_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "ai-drama-skills-v2", "knowledge", "learned-rules-log.json",
))


def _load_pattern_log() -> Dict[str, Any]:
    """加载经验模式统计日志。"""
    try:
        if os.path.exists(_PATTERN_LOG_PATH):
            with open(_PATTERN_LOG_PATH, encoding="utf-8") as f:
                return json.load(f)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[LearnedRules] 加载模式日志失败: %s", exc)
    return {"patterns": {}, "last_updated": ""}


def _save_pattern_log(log: Dict[str, Any]) -> None:
    """保存经验模式统计日志。"""
    try:
        log["last_updated"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(_PATTERN_LOG_PATH), exist_ok=True)
        with open(_PATTERN_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[LearnedRules] 保存模式日志失败: %s", exc)


def _append_learned_rule(rule: Dict[str, Any]) -> None:
    """将新发现的经验规则追加到 learned-rules.md。"""
    try:
        os.makedirs(os.path.dirname(_LEARNED_RULES_PATH), exist_ok=True)
        if not os.path.exists(_LEARNED_RULES_PATH):
            _create_learned_rules_skeleton()

        entry = (
            f"\n## [{rule['id']}] {rule['title']}\n\n"
            f"> **触发条件**: {rule['trigger']}\n"
            f"> **发现时间**: {rule['discovered_at']}\n"
            f"> **置信度**: {rule['confidence']} (出现 {rule['occurrence']} 次)\n"
            f"> **关联维度**: {', '.join(rule.get('dimensions', []))}\n\n"
            f"**描述**: {rule['description']}\n\n"
            f"**建议动作**:\n"
        )
        for action in rule.get("suggested_actions", []):
            entry += f"- {action}\n"
        entry += "\n---\n"

        with open(_LEARNED_RULES_PATH, "a", encoding="utf-8") as f:
            f.write(entry)

        logger.info("[LearnedRules] 新增经验规则: %s", rule['id'])
    except Exception as exc:  # noqa: BLE001
        logger.warning("[LearnedRules] 写入 learned-rules.md 失败: %s", exc)


def _create_learned_rules_skeleton() -> None:
    """创建 learned-rules.md 骨架文件。"""
    content = """# knowledge/learned-rules.md — 跨项目经验沉淀库

> **架构说明**（来自 Novel-to-Script-Team knowledge-curator 理念）
>
> 本文件记录系统从多个项目创作过程中自动沉淀的经验规则。
> 当某类失败模式在多个项目中重复出现（≥3次），系统自动分析并写入。
>
> - **置信度 A**: 出现 ≥ 10 次，强制执行
> - **置信度 B**: 出现 5-9 次，强烈建议
> - **置信度 C**: 出现 3-4 次，参考建议
> - **更新机制**: ConvergenceService 停机时自动触发模式检测

## 使用规范

| Skill | 引用方式 |
|-------|---------|
| drama-quality-suite | 读取 A/B 级规则作为硬检查项 |
| drama-evaluation-scorer | 读取 A/B 级规则作为扣分依据 |
| drama-creator-core | 读取 C 级及以上规则作为创作预警 |
| drama-continuity-recorder | 读取与连续性相关的规则 |

---

<!-- 自动生成内容开始，勿手动编辑以下条目格式 -->

"""
    with open(_LEARNED_RULES_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def record_convergence_failure(
    project_id: int,
    project_title: str,
    failed_dimensions: List[str],
    convergence_state: str,
    fix_round: int,
    score_history: List[float],
    genre: str = "",
) -> Optional[Dict[str, Any]]:
    """
    记录一次收敛失败事件，检测是否形成跨项目模式。

    - 将失败信息写入 pattern_log
    - 若同类模式达到阈值（_PATTERN_THRESHOLD），沉淀为 learned-rules.md 条目
    - 返回新沉淀的规则字典（若无新规则则返回 None）

    由 ConvergenceService.record_score() 在状态变为 blocked 时调用。
    """
    if not failed_dimensions:
        return None

    log = _load_pattern_log()
    patterns = log.setdefault("patterns", {})

    # 用失败维度集合作为模式 key
    pattern_key = "|".join(sorted(failed_dimensions))
    if genre:
        pattern_key = f"{genre}:{pattern_key}"

    entry = patterns.setdefault(pattern_key, {
        "dimensions": sorted(failed_dimensions),
        "genre": genre,
        "occurrences": [],
        "rule_written": False,
    })

    entry["occurrences"].append({
        "project_id": project_id,
        "project_title": project_title,
        "convergence_state": convergence_state,
        "fix_round": fix_round,
        "score_history": score_history,
        "timestamp": datetime.now().isoformat(),
    })

    occurrence_count = len(entry["occurrences"])
    _save_pattern_log(log)

    # 达到阈值且未写入过规则
    if occurrence_count >= _PATTERN_THRESHOLD and not entry["rule_written"]:
        rule = _synthesize_rule(pattern_key, entry, occurrence_count)
        _append_learned_rule(rule)
        entry["rule_written"] = True
        _save_pattern_log(log)
        return rule
    elif occurrence_count >= _PATTERN_THRESHOLD * 2 and entry["rule_written"]:
        # 出现次数翻倍时升级置信度
        logger.info(
            "[LearnedRules] 模式 %s 出现 %d 次，置信度升级",
            pattern_key, occurrence_count,
        )

    return None


def _synthesize_rule(
    pattern_key: str,
    entry: Dict[str, Any],
    occurrence: int,
) -> Dict[str, Any]:
    """从失败模式合成规则条目。"""
    dimensions = entry.get("dimensions") or []
    genre = entry.get("genre") or "通用"

    confidence = "C"
    if occurrence >= 10:
        confidence = "A"
    elif occurrence >= 5:
        confidence = "B"

    # 根据维度生成具体建议
    suggested_actions = _generate_suggested_actions(dimensions, genre)

    rule_id = f"LR-{datetime.now().strftime('%Y%m')}-{pattern_key[:20].replace('|', '-').replace(':', '-')}"
    title = f"{genre}题材中 {'+'.join(dimensions)} 维度持续失败"

    return {
        "id": rule_id,
        "title": title,
        "trigger": f"多个项目收敛停机时检测到 {'+'.join(dimensions)} 维度重复失败",
        "discovered_at": datetime.now().strftime("%Y-%m-%d"),
        "confidence": confidence,
        "occurrence": occurrence,
        "dimensions": dimensions,
        "genre": genre,
        "description": (
            f"在 {genre} 题材项目中，{'+'.join(dimensions)} 维度出现 {occurrence} 次收敛失败。"
            f"这表明当前创作流程在这些维度存在系统性问题，需要针对性优化。"
        ),
        "suggested_actions": suggested_actions,
    }


def _generate_suggested_actions(dimensions: List[str], genre: str) -> List[str]:
    """根据失败维度生成具体建议动作。"""
    actions = []
    dim_actions: Dict[str, str] = {
        "pacing": "在大纲阶段增加节奏约束（每3集一个情绪高点），避免平铺直叙",
        "plot_structure": "强化三幕剧结构约束，确保第1/3处有明显转折点",
        "quality_guard": "增加 AI 痕迹检测前置步骤，在剧本生成时注入更多短剧专属表达",
        "compliance": f"为 {genre} 题材建立专属合规预检查清单，提前规避高风险内容",
        "content_safety": "在 ScriptAgent 系统提示中增加内容安全红线说明",
    }
    for dim in dimensions:
        if dim in dim_actions:
            actions.append(dim_actions[dim])

    if len(dimensions) > 2:
        actions.append("考虑拆分修复回路：先修复合规/安全问题，再修复内容质量问题")

    if genre and genre != "通用":
        actions.append(f"在 knowledge/genres/{genre}.md 中添加针对这类问题的预防指南")

    return actions or ["审查当前创作约束配置，增强对该维度的检测精度"]
