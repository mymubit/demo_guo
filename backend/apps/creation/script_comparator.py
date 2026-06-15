# -*- coding: utf-8 -*-
"""ScriptComparator：爆款剧本基线比对服务。

来自 Novel-to-Script-Team script-comparator 设计理念：
  - 不仅评估「绝对分数」，还评估与 Top-N 爆款的「相对差距」
  - 选取同题材 Top-3 S 级爆款作为基线
  - 逐维度比较，输出具体差距量化 + 优先修复建议
  - 结果写入 comparator_report artifact
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_SKILLS_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "ai-drama-skills-v2",
))
_CATALOG_PATH = os.path.join(_SKILLS_ROOT, "drama-knowledge-base", "config", "爆款剧本库.json")
_S_GRADE_CACHE_DIR = os.path.join(_SKILLS_ROOT, ".cache", "s-grade-scores")

# 比对维度配置（来自 s-grade-scores 的 dimensions 字段）
_COMPARE_DIMENSIONS = [
    "dramaGene",
    "paymentCard",
    "structural",
    "detailPolish",
    "emotionalDesign",
]

# 各维度的友好名称
_DIMENSION_LABELS = {
    "dramaGene": "短剧基因",
    "paymentCard": "付费刺激",
    "structural": "结构与世界观",
    "detailPolish": "细节打磨",
    "emotionalDesign": "情绪设计",
}


def _load_catalog() -> Dict[str, Any]:
    """加载爆款剧本库目录。"""
    try:
        with open(_CATALOG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptComparator] 无法加载爆款剧本库: %s", exc)
        return {}


def _load_s_grade_score(script_id: str) -> Optional[Dict[str, Any]]:
    """加载 S 级剧本的缓存评分报告。"""
    cache_file = os.path.join(_S_GRADE_CACHE_DIR, f"{script_id}-deep.json")
    try:
        if os.path.exists(cache_file):
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptComparator] 无法加载 %s 缓存: %s", script_id, exc)
    return None


def _select_top_baselines(
    catalog: Dict[str, Any],
    genre: str,
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """
    从爆款剧本库选取同题材 Top-N S 级剧本作为基线。
    若同题材不足 top_n，补充其他题材 S 级剧本。
    """
    scripts = catalog.get("scripts") or []
    s_grade = [s for s in scripts if s.get("grade") == "S" and s.get("enabled", True)]

    same_genre = [s for s in s_grade if s.get("genre") == genre]
    other_genre = [s for s in s_grade if s.get("genre") != genre]

    selected = same_genre[:top_n]
    if len(selected) < top_n:
        selected.extend(other_genre[:top_n - len(selected)])

    # 加载评分缓存
    baselines = []
    for script in selected:
        score_data = _load_s_grade_score(script["id"])
        if score_data:
            baselines.append({
                "id": script["id"],
                "title": script.get("title") or script["id"],
                "genre": script.get("genre") or "",
                "score_total": script.get("score_total") or 0,
                "play_count": script.get("play_count") or "",
                "finalScore": score_data.get("finalScore") or 0,
                "fiveDimensionScore": score_data.get("fiveDimensionScore") or 0,
                "dimensions": score_data.get("dimensions") or {},
                "sameGenre": script.get("genre") == genre,
            })
    return baselines


def _extract_dimension_score(score_report: Dict[str, Any], dim_key: str) -> Optional[float]:
    """从评分报告中提取特定维度的分数。"""
    dimensions = score_report.get("dimensions") or {}
    if dim_key in dimensions:
        d = dimensions[dim_key]
        if isinstance(d, (int, float)):
            return float(d)
        if isinstance(d, dict):
            return float(d.get("score") or 0)
    # 兼容旧字段
    alt_keys = {
        "dramaGene": ["dramaGene", "drama_gene", "shortDramaGene"],
        "paymentCard": ["paymentCard", "payment_card", "cardScore"],
        "structural": ["structural", "structure"],
        "detailPolish": ["detailPolish", "detail_polish", "polish"],
        "emotionalDesign": ["emotionalDesign", "emotion_design", "emotion"],
    }
    for key in alt_keys.get(dim_key, []):
        if key in score_report:
            val = score_report[key]
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, dict):
                return float(val.get("score") or 0)
    return None


def _compute_gap(current_score: Optional[float], baseline_score: float) -> Dict[str, Any]:
    """计算与基线的差距。"""
    if current_score is None:
        return {"current": None, "baseline": baseline_score, "gap": None, "status": "unknown"}
    gap = baseline_score - current_score
    if gap <= 0:
        status = "above_baseline"
    elif gap <= 5:
        status = "near_baseline"
    elif gap <= 15:
        status = "below_baseline"
    else:
        status = "far_below_baseline"
    return {
        "current": round(current_score, 1),
        "baseline": round(baseline_score, 1),
        "gap": round(gap, 1),
        "status": status,
    }


def _generate_priority_fixes(
    dimension_gaps: Dict[str, Any],
    genre: str,
) -> List[Dict[str, Any]]:
    """根据维度差距生成优先修复建议（按差距大小排序）。"""
    fixes = []
    for dim_key, gap_info in dimension_gaps.items():
        gap = gap_info.get("avg_gap")
        if gap is None or gap <= 0:
            continue
        label = _DIMENSION_LABELS.get(dim_key, dim_key)
        priority = "高" if gap > 15 else ("中" if gap > 5 else "低")
        fix_suggestions = _get_fix_suggestions(dim_key, gap, genre)
        fixes.append({
            "dimension": dim_key,
            "dimensionLabel": label,
            "avgGap": round(gap, 1),
            "priority": priority,
            "suggestions": fix_suggestions,
        })

    # 按差距降序排序
    fixes.sort(key=lambda x: x["avgGap"], reverse=True)
    return fixes[:5]


def _get_fix_suggestions(dim_key: str, gap: float, genre: str) -> List[str]:
    """针对维度差距生成具体修复建议。"""
    suggestions_map = {
        "dramaGene": [
            "增加集末悬念钩子密度（目标：每集结尾都有强卡点）",
            f"参考 {genre} 题材爆款的冲突节奏，缩短铺垫时长",
            "检查对话口语化程度，减少书面表达",
        ],
        "paymentCard": [
            "在第 1/3 集强化情绪爆点，为付费墙做情绪蓄力",
            "确保付费墙前 1 集以高悬念或强爽感结尾",
            "增加付费点周边的「钩子强度」评估",
        ],
        "structural": [
            "检查三幕结构是否清晰（开篇钩/中段反转/高潮爆发）",
            "加强角色行为逻辑自洽性，减少为剧情服务的 OOC",
            "确认世界观设定的一致性（人设卡/世界观文档对齐）",
        ],
        "detailPolish": [
            "提高台词口语化密度（目标：每分钟 80-120 字）",
            "丰富动作描写（△ 行数比例目标 ≥ 30%）",
            "检查场景描写清晰度，确保可拍摄性",
        ],
        "emotionalDesign": [
            "引入 EmotionArchitect 生成逐集情绪节点，避免情绪平淡",
            "参考 insight_report 的 reversalPoints，增强情感反转设计",
            "确保每3集有一个「情绪高潮」节点",
        ],
    }
    base = suggestions_map.get(dim_key, [f"提升 {_DIMENSION_LABELS.get(dim_key, dim_key)} 得分"])
    if gap > 20:
        base.insert(0, f"⚠️ 与爆款差距较大（{gap:.1f}分），建议重点优化本维度")
    return base[:3]


def run_script_comparator(
    project: "Project",  # type: ignore[name-defined]
    genre: str = "",
    top_n: int = 3,
) -> Dict[str, Any]:
    """
    执行爆款基线比对分析。

    读取当前项目的 script_score_report / score_report artifact，
    与同题材 Top-N 爆款逐维度比较，返回结构化差距报告。
    """
    from ..artifact_service import get_artifact, save_artifact

    score_report = get_artifact(project, "script_score_report") or get_artifact(project, "score_report") or {}
    if not genre:
        brief = get_artifact(project, "project_brief") or {}
        genre = brief.get("genre") or ""

    catalog = _load_catalog()
    if not catalog:
        logger.warning("[ScriptComparator] 爆款剧本库加载失败，跳过比对 project=%s", project.id)
        return {
            "agentId": "script_comparator",
            "status": "skipped",
            "reason": "爆款剧本库不可用",
        }

    baselines = _select_top_baselines(catalog, genre, top_n=top_n)
    if not baselines:
        logger.warning("[ScriptComparator] 无可用基线，跳过 project=%s", project.id)
        return {
            "agentId": "script_comparator",
            "status": "skipped",
            "reason": "无可用 S 级基线",
        }

    current_final = (
        score_report.get("finalScore")
        or score_report.get("overallScore")
        or score_report.get("fiveDimensionScore")
    )
    if current_final is not None:
        current_final = float(current_final)

    # 逐维度比较
    dimension_gaps: Dict[str, Any] = {}
    for dim_key in _COMPARE_DIMENSIONS:
        current_score = _extract_dimension_score(score_report, dim_key)
        baseline_scores = []
        for baseline in baselines:
            baseline_dim = _extract_dimension_score(baseline, dim_key)
            if baseline_dim is not None:
                baseline_scores.append(baseline_dim)

        if not baseline_scores:
            continue

        avg_baseline = sum(baseline_scores) / len(baseline_scores)
        max_baseline = max(baseline_scores)
        gap_vs_avg = _compute_gap(current_score, avg_baseline)

        dimension_gaps[dim_key] = {
            "label": _DIMENSION_LABELS.get(dim_key, dim_key),
            "current": gap_vs_avg["current"],
            "avgBaseline": round(avg_baseline, 1),
            "maxBaseline": round(max_baseline, 1),
            "avg_gap": gap_vs_avg["gap"],
            "status": gap_vs_avg["status"],
            "baselineDetails": [
                {
                    "title": b["title"],
                    "score": _extract_dimension_score(b, dim_key),
                    "sameGenre": b["sameGenre"],
                }
                for b in baselines
            ],
        }

    # 总分比较
    avg_final = sum(b["finalScore"] for b in baselines) / len(baselines) if baselines else 0
    final_gap = _compute_gap(current_final, avg_final)

    # 生成优先修复建议
    priority_fixes = _generate_priority_fixes(dimension_gaps, genre)

    report: Dict[str, Any] = {
        "agentId": "script_comparator",
        "projectId": str(project.id),
        "genre": genre,
        "finalScore": {
            "current": round(current_final, 1) if current_final is not None else None,
            "avgBaseline": round(avg_final, 1),
            "gap": final_gap.get("gap"),
            "status": final_gap.get("status"),
        },
        "baselines": [
            {
                "id": b["id"],
                "title": b["title"],
                "genre": b["genre"],
                "finalScore": b["finalScore"],
                "sameGenre": b["sameGenre"],
                "playCount": b.get("play_count") or "",
            }
            for b in baselines
        ],
        "dimensionGaps": dimension_gaps,
        "priorityFixes": priority_fixes,
        "summary": {
            "totalGap": round(final_gap.get("gap") or 0, 1),
            "weakestDimension": priority_fixes[0]["dimensionLabel"] if priority_fixes else "",
            "isAboveAvgBaseline": (final_gap.get("gap") or 0) <= 0,
            "fixableInOneRound": sum(
                1 for f in priority_fixes if f.get("priority") == "高"
            ),
        },
    }

    save_artifact(project, "comparator_report", report)
    logger.info(
        "[ScriptComparator] project=%s genre=%s finalGap=%.1f weakest=%s",
        project.id,
        genre,
        report["summary"]["totalGap"],
        report["summary"]["weakestDimension"],
    )
    return report
