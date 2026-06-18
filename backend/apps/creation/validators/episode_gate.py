# -*- coding: utf-8 -*-
"""
Python-native episode and full-script quality gate.
  + detection/episode-gate.js
  + detection/script-output-guards.js
  + detection/format-metrics.js

直接接受内存中的 episode dict（来自 episode_scripts artifact），
无文件 I/O，无 Node 依赖。

对外接口：
    validate_episode(ep, outline_episodes=None) -> ValidationResult      # 逐集模式
    validate_episodes_full(episodes, expected_count=None) -> ValidationResult  # 全书模式
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .result import ValidationResult

# ── 阈值常量（同步自 skill-thresholds.json: outputCompleteness）─────────────────
_FIRST_EP_MIN_WORDS = 1000
_OTHER_EP_MIN_WORDS = 800
_WORD_COUNT_TOLERANCE = 100
_MIN_DIALOGUES_PER_EP = 5
_MIN_SUBSTANTIVE_DIALOGUES = 4
_MIN_SUBSTANTIVE_DIALOGUE_CHARS = 6
_MIN_DIALOGUE_RATIO = 0.28
_MIN_SCENES_PER_EP = 1
_MAX_SCENES_PER_EP = 3
_PAY_WINDOW = (8, 9, 10)

# 场景头正则：匹配 "1-1 室内/室外 地点" 格式（商业短剧 SSOT）
_COMMERCIAL_SCENE_HEADER_RE = re.compile(
    r"^\s*\d+-\d+\s+[\u4e00-\u9fff]",
    re.MULTILINE,
)

# 待填占位符
_PLACEHOLDER_RES = [
    re.compile(r"\[.+?\]"),
    re.compile(r"【待(填|写|补充|扩写)[^】]*】"),
    re.compile(r"（待(填|写|补充|扩写)[^）]*）"),
    re.compile(r"此处扩写|待扩写|待补充|TODO|TBD"),
]

# 对白行：以角色名+冒号开头
_DIALOGUE_RE = re.compile(r"^[\u4e00-\u9fff\w]{1,10}[：:]", re.MULTILINE)

# CJK 字符计数
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _cjk_count(text: str) -> int:
    return len(_CJK_RE.findall(text))


def _count_dialogues(text: str) -> int:
    return len(_DIALOGUE_RE.findall(text))


def _count_substantive_dialogues(text: str) -> int:
    """台词字符数 ≥ _MIN_SUBSTANTIVE_DIALOGUE_CHARS 的对白数。"""
    count = 0
    for line in text.splitlines():
        m = _DIALOGUE_RE.match(line)
        if m:
            content = line[m.end():].strip()
            if _cjk_count(content) >= _MIN_SUBSTANTIVE_DIALOGUE_CHARS:
                count += 1
    return count


def _count_scenes(text: str) -> int:
    return len(_COMMERCIAL_SCENE_HEADER_RE.findall(text))


def _has_placeholder(text: str) -> bool:
    return any(p.search(text) for p in _PLACEHOLDER_RES)


def _dialogue_ratio(text: str) -> float:
    total_cjk = _cjk_count(text)
    if total_cjk == 0:
        return 0.0
    dialogue_cjk = 0
    for line in text.splitlines():
        if _DIALOGUE_RE.match(line):
            dialogue_cjk += _cjk_count(line)
    return dialogue_cjk / total_cjk


def _get_episode_text(ep: Dict[str, Any]) -> str:
    for key in ("scriptMarkdown", "full_script_text", "content"):
        val = (ep.get(key) or "").strip()
        if val:
            return val
    return ""


def _ep_num(ep: Dict[str, Any]) -> int:
    try:
        return int(ep.get("episodeNumber") or ep.get("episode") or 0)
    except (TypeError, ValueError):
        return 0


# ── 逐集校验 ─────────────────────────────────────────────────────────────────

def validate_episode(
    ep: Dict[str, Any],
    *,
    outline_episodes: Optional[List[Dict[str, Any]]] = None,
) -> ValidationResult:
    """
    逐集质量闸门。

    Args:
        ep: episode_scripts.episodes[i] 字典
        outline_episodes: series_outline.episodes 列表（可选，用于大纲对齐检测）
    """
    ep_num = _ep_num(ep)
    text = _get_episode_text(ep)
    issues: List[str] = []

    # ── 1. 字数 ──
    words = _cjk_count(text)
    min_words = (_FIRST_EP_MIN_WORDS if ep_num <= 1 else _OTHER_EP_MIN_WORDS) - _WORD_COUNT_TOLERANCE
    if words < min_words:
        issues.append(f"第{ep_num}集字数不足（{words} 字，要求 ≥{min_words} 字）")

    # ── 2. 台词数量 ──
    dialogues = _count_dialogues(text)
    if dialogues < _MIN_DIALOGUES_PER_EP:
        issues.append(f"第{ep_num}集台词过少（{dialogues} 句，要求 ≥{_MIN_DIALOGUES_PER_EP} 句）")

    substantive = _count_substantive_dialogues(text)
    if substantive < _MIN_SUBSTANTIVE_DIALOGUES:
        issues.append(
            f"第{ep_num}集有效台词过少（{substantive} 句实质内容，要求 ≥{_MIN_SUBSTANTIVE_DIALOGUES}）"
        )

    # ── 3. 台词占比 ──
    ratio = _dialogue_ratio(text)
    if ratio < _MIN_DIALOGUE_RATIO:
        issues.append(
            f"第{ep_num}集台词占比偏低（{ratio:.1%}，要求 ≥{_MIN_DIALOGUE_RATIO:.0%}）"
        )

    # ── 4. 场景数 ──
    scenes = _count_scenes(text)
    if scenes < _MIN_SCENES_PER_EP:
        issues.append(f"第{ep_num}集缺少商业场景头（0个，要求 ≥{_MIN_SCENES_PER_EP}）")
    elif scenes > _MAX_SCENES_PER_EP:
        issues.append(
            f"第{ep_num}集场景数过多（{scenes}个，建议 ≤{_MAX_SCENES_PER_EP}）"
        )

    # ── 5. 占位符 ──
    if _has_placeholder(text):
        issues.append(f"第{ep_num}集含待填占位符，须在发布前替换")

    # ── 6. 付费窗口提示 ──
    if ep_num in _PAY_WINDOW and not _has_strong_cliffhanger(text):
        issues.append(
            f"第{ep_num}集处于付费窗口（第8-10集），建议强化集末钩子/截断对白"
        )

    # ── 7. 大纲对齐（可选） ──
    if outline_episodes:
        outline_issue = _check_outline_alignment(ep_num, text, outline_episodes)
        if outline_issue:
            issues.append(outline_issue)

    if issues:
        return ValidationResult.fail(issues, sub_skill="sub-gate")
    return ValidationResult.ok(sub_skill="sub-gate")


def _has_strong_cliffhanger(text: str) -> bool:
    """集末是否有明显钩子（截断对白、强感叹、问句）。"""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    last_lines = lines[-5:] if len(lines) >= 5 else lines
    last_text = "\n".join(last_lines)
    return bool(
        re.search(r"[！!？?…]{1,3}\s*$", last_text)
        or re.search(r"[\u4e00-\u9fff]{2,}[：:]\s*$", last_text)
    )


def _check_outline_alignment(
    ep_num: int,
    script_text: str,
    outline_episodes: List[Dict[str, Any]],
) -> Optional[str]:
    outline_ep = next(
        (e for e in outline_episodes if _ep_num(e) == ep_num), None
    )
    if not outline_ep:
        return f"分集大纲缺少第{ep_num}集条目（动笔前须有大纲对应段）"

    summary = (outline_ep.get("oneLineSummary") or outline_ep.get("summary") or "").strip()
    if _cjk_count(summary) < 30:
        return f"分集大纲第{ep_num}集过短（约{_cjk_count(summary)}字），建议 ≥30 字再扩写"

    return None


# ── 全书完整性校验 ──────────────────────────────────────────────────────────

def validate_episodes_full(
    episodes: List[Dict[str, Any]],
    *,
    expected_count: Optional[int] = None,
) -> ValidationResult:
    """
    全书交付完整性检测（对应 sub-gate --full 模式）。

    Args:
        episodes: episode_scripts.episodes 列表
        expected_count: 期望总集数（来自 project.episode_count）
    """
    issues: List[str] = []
    valid_episodes = [ep for ep in episodes if isinstance(ep, dict) and _ep_num(ep) > 0]
    actual_count = len(valid_episodes)

    if expected_count and actual_count < expected_count:
        ratio = actual_count / expected_count
        issues.append(
            f"剧本集数不足：已生成 {actual_count} 集，期望 {expected_count} 集"
            f"（完成率 {ratio:.0%}）"
        )

    empty_episodes = []
    for ep in valid_episodes:
        text = _get_episode_text(ep)
        if _cjk_count(text) < 100:
            empty_episodes.append(_ep_num(ep))

    if empty_episodes:
        nums = "、".join(str(n) for n in sorted(empty_episodes)[:5])
        issues.append(f"以下集数内容为空或过短：第{nums}集")

    if issues:
        return ValidationResult.fail(issues, sub_skill="sub-gate-full")
    return ValidationResult.ok(sub_skill="sub-gate-full")
