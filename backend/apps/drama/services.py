# -*- coding: utf-8 -*-
"""Drama Skills 核心服务层。"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class DramaWordCountService:
    """字数治理服务 — 行业字数硬标准执行。"""

    # 行业标准参数（来自 dramaskilltrae skill-thresholds.json）
    FIRST_EPISODE_MIN = 900
    FIRST_EPISODE_MAX = 1100
    OTHER_EPISODE_MIN = 700
    OTHER_EPISODE_MAX = 900
    DIALOGUE_RATIO_MIN = 0.28
    MAX_SCENES = 3

    # 非剧本内容的过滤模式（AI绘图提示词块等）
    NON_SCRIPT_PATTERNS = [
        r"```.*?```",          # 代码块（AI提示词通常在此）
        r"<!--.*?-->",         # HTML注释
        r"\[AI提示词\].*?\[/AI提示词\]",  # 自定义AI提示词块
        r"【付费卡点】.*?【/付费卡点】",
        r"【悬念钩子】.*?【/悬念钩子】",
        r"## 润色报告.*?---",  # 润色报告块
    ]

    # 台词格式：角色（情绪）：台词内容
    DIALOGUE_PATTERN = re.compile(r'^[^\n]+（[^）]+）：(.+)$', re.MULTILINE)

    # 场景头格式：数字-数字 时间 内外 地点
    SCENE_HEAD_PATTERN = re.compile(r'^\d+-\d+\s+[日夜晨昏]\s+[内外]\s+.+$', re.MULTILINE)

    @classmethod
    def clean_non_script(cls, content: str) -> str:
        """清除非剧本内容，获取纯剧本文本。"""
        cleaned = content
        for pattern in cls.NON_SCRIPT_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    @classmethod
    def count_cjk(cls, text: str) -> int:
        """统计CJK字符数量（中日韩字符）。"""
        return sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')

    @classmethod
    def count_dialogue_cjk(cls, text: str) -> int:
        """统计台词部分的CJK字符数量。"""
        dialogues = cls.DIALOGUE_PATTERN.findall(text)
        return sum(cls.count_cjk(d) for d in dialogues)

    @classmethod
    def count_scenes(cls, text: str) -> int:
        """统计场景数量。"""
        return len(cls.SCENE_HEAD_PATTERN.findall(text))

    @classmethod
    def validate_episode(cls, content: str, episode_number: int) -> Dict[str, Any]:
        """
        验证单集字数是否达标。

        返回格式：
        {
            "episode": 1,
            "word_count": {"total": 1050, "target_range": [900, 1100], "status": "✅达标"},
            "dialogue_ratio": {"count": 320, "ratio": "30.5%", "target": "≥28%", "status": "✅达标"},
            "scene_count": {"count": 2, "target": "1-3", "status": "✅达标"},
            "overall": "通过",
            "recommendations": []
        }
        """
        cleaned = cls.clean_non_script(content)

        total_cjk = cls.count_cjk(cleaned)
        dialogue_cjk = cls.count_dialogue_cjk(cleaned)
        scene_count = cls.count_scenes(cleaned)

        # 字数范围
        if episode_number == 1:
            min_words, max_words = cls.FIRST_EPISODE_MIN, cls.FIRST_EPISODE_MAX
        else:
            min_words, max_words = cls.OTHER_EPISODE_MIN, cls.OTHER_EPISODE_MAX

        # 台词占比
        dialogue_ratio = dialogue_cjk / total_cjk if total_cjk > 0 else 0

        # 判定
        word_ok = min_words <= total_cjk <= max_words
        dialogue_ok = dialogue_ratio >= cls.DIALOGUE_RATIO_MIN
        scene_ok = 1 <= scene_count <= cls.MAX_SCENES

        word_status = "✅达标" if word_ok else ("❌偏短" if total_cjk < min_words else "⚠️偏长")
        dialogue_status = "✅达标" if dialogue_ok else "❌台词不足"
        scene_status = "✅达标" if scene_ok else ("⚠️场景过多" if scene_count > cls.MAX_SCENES else "⚠️无场景")

        recommendations = []
        if not word_ok:
            if total_cjk < min_words:
                deficit = min_words - total_cjk
                recommendations.append(
                    f"字数偏短（缺{deficit}字）：建议延伸情绪高点场景、增加对峙来回台词、增加环境/道具细节描写"
                )
            else:
                surplus = total_cjk - max_words
                recommendations.append(
                    f"字数偏长（多{surplus}字）：建议删除重复△动作行、压缩过渡场景、删除无功能过渡台词"
                )

        if not dialogue_ok:
            actual_pct = f"{dialogue_ratio:.1%}"
            recommendations.append(
                f"台词占比不足（{actual_pct}<28%）：建议将部分△动作改为台词传达、增加角色间的简短交锋"
            )

        if scene_count > cls.MAX_SCENES:
            recommendations.append(
                f"场景数量过多（{scene_count}>3）：建议合并功能相近的相邻小场景"
            )

        overall = "通过" if (word_ok and dialogue_ok and scene_ok) else "不通过"

        return {
            "episode": episode_number,
            "word_count": {
                "total": total_cjk,
                "target_range": [min_words, max_words],
                "deviation": total_cjk - min_words if total_cjk < min_words else (
                    total_cjk - max_words if total_cjk > max_words else 0
                ),
                "status": word_status,
            },
            "dialogue_ratio": {
                "dialogue_count": dialogue_cjk,
                "ratio": f"{dialogue_ratio:.1%}",
                "target": f"≥{cls.DIALOGUE_RATIO_MIN:.0%}",
                "status": dialogue_status,
            },
            "scene_count": {
                "count": scene_count,
                "target": f"1-{cls.MAX_SCENES}",
                "status": scene_status,
            },
            "overall": overall,
            "recommendations": recommendations,
        }

    @classmethod
    def validate_all_episodes(cls, episodes: Dict[int, str]) -> Dict[str, Any]:
        """
        批量验证所有集的字数。

        参数：
        - episodes: {episode_number: content}

        返回：
        {
            "summary": {"total": 30, "pass": 28, "fail": 2, "avg_words": 835},
            "episodes": [每集报告],
            "issues": [不达标集数列表]
        }
        """
        reports = []
        total_words = 0
        pass_count = 0
        issues = []

        for ep_num, content in sorted(episodes.items()):
            report = cls.validate_episode(content, ep_num)
            reports.append(report)
            total_words += report["word_count"]["total"]
            if report["overall"] == "通过":
                pass_count += 1
            else:
                issues.append({"episode": ep_num, "issues": report["recommendations"]})

        total = len(episodes)
        avg_words = total_words // total if total > 0 else 0

        return {
            "summary": {
                "total_episodes": total,
                "pass_count": pass_count,
                "fail_count": total - pass_count,
                "pass_rate": f"{pass_count / total:.1%}" if total > 0 else "N/A",
                "avg_words": avg_words,
                "total_words": total_words,
            },
            "episodes": reports,
            "issues": issues,
        }


class DramaRoleService:
    """Drama Skills 角色管理服务。"""

    # 角色三层分级标签（用于前端展示）
    TIER_LABELS = {
        1: {"name": "核心必需", "desc": "快速通道，所有项目必须执行", "color": "blue"},
        2: {"name": "优化推荐", "desc": "显著提升作品质量，按需选用", "color": "green"},
        3: {"name": "专项增强", "desc": "特定场景专用，按项目需求选用", "color": "gray"},
    }

    @staticmethod
    def get_all_roles_grouped() -> List[Dict[str, Any]]:
        """
        获取35个角色，按部门分组，并附加三层分级信息。

        tier字段说明：
          1 = 核心必需（快速通道8个，任何项目必做）
          2 = 优化推荐（约12个，能显著提升质量）
          3 = 专项增强（约15个，特定需求时选用）
        """
        from apps.agent.models import AgentDefinition, AgentLlmRouteConfig
        from apps.drama.defaults import (
            DRAMA_DEPARTMENTS, DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS,
        )

        # 从 defaults 中获取 tier 信息（tier字段在defaults中已定义）
        tier_map = {r["agent_id"]: r.get("tier", 3) for r in DRAMA_ROLE_DEFAULTS}

        defaults_by_id = {role["agent_id"]: role for role in DRAMA_ROLE_DEFAULTS}

        agents = list(
            AgentDefinition.objects.filter(
                agent_id__startswith="drama.",
                is_enabled=True,
            ).order_by("workspace_order", "agent_id")
        )

        routes = {
            r.route_key: r
            for r in AgentLlmRouteConfig.objects.filter(
                route_key__startswith="drama."
            ).select_related("llm_provider")
        }

        def resolve_dept_code(agent: AgentDefinition) -> str | None:
            ui_schema = agent.ui_schema if isinstance(agent.ui_schema, dict) else {}
            dept_code = ui_schema.get("dept")
            if dept_code:
                return dept_code
            meta = defaults_by_id.get(agent.agent_id)
            return meta.get("dept") if meta else None

        result = []
        for dept in sorted(DRAMA_DEPARTMENTS, key=lambda d: d["order"]):
            dept_roles = []
            for agent in agents:
                if resolve_dept_code(agent) != dept["code"]:
                    continue

                agent_id = agent.agent_id
                route = routes.get(agent_id)
                model_name = "未配置"
                if route and route.llm_provider:
                    model_name = route.llm_provider.name
                elif route and route.display_name:
                    model_name = route.display_name

                tier = tier_map.get(agent_id, 3)

                dept_roles.append({
                    "agent_id": agent_id,
                    # 只返回中文名，不再暴露英文name字段
                    "name_zh": agent.name_zh,
                    "description": agent.description,
                    "workspace_order": agent.workspace_order,
                    "is_fast_track": agent_id in DRAMA_FAST_TRACK_ROLES,
                    "tier": tier,
                    "tier_label": DramaRoleService.TIER_LABELS[tier]["name"],
                    "tier_color": DramaRoleService.TIER_LABELS[tier]["color"],
                    "is_enabled": agent.is_enabled,
                    "current_model": model_name,
                    "input_contract": agent.input_contract,
                    "output_contract": agent.output_contract,
                    "runtime_policy": agent.runtime_policy,
                })

            if dept_roles:
                result.append({
                    "dept_code": dept["code"],
                    "dept_name": dept["name_zh"],
                    "dept_order": dept["order"],
                    "roles": sorted(dept_roles, key=lambda r: (r["tier"], r["workspace_order"])),
                    "tier_summary": {
                        1: sum(1 for r in dept_roles if r["tier"] == 1),
                        2: sum(1 for r in dept_roles if r["tier"] == 2),
                        3: sum(1 for r in dept_roles if r["tier"] == 3),
                    },
                })

        return result

    @staticmethod
    def get_token_stats(user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        获取Token用量统计。

        返回按角色/时间/项目维度的统计数据。
        """
        from datetime import timedelta

        from django.db.models import Avg, Count, Sum
        from django.utils import timezone

        from apps.drama.models import DramaRoleExecution

        cutoff = timezone.now() - timedelta(days=days)
        qs = DramaRoleExecution.objects.filter(
            created_at__gte=cutoff,
            status=DramaRoleExecution.Status.SUCCESS,
        )

        if user_id:
            qs = qs.filter(drama_project__user_id=user_id)

        # 按角色聚合（注意：先values再annotate，避免聚合嵌套问题）
        from django.db.models import FloatField, ExpressionWrapper
        by_role = list(
            qs.values("agent_id", "agent_name_zh")
            .annotate(
                total_calls=Count("id"),
                total_tokens=Sum("total_tokens"),
                total_cost_cents=Sum("cost_cents"),
            )
            .order_by("-total_tokens")
        )
        # 手动计算avg_tokens
        for item in by_role:
            item["avg_tokens"] = (item["total_tokens"] or 0) / max(item["total_calls"], 1)

        # 按天聚合（最近30天）
        from django.db.models.functions import TruncDate

        by_day = list(
            qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                total_tokens=Sum("total_tokens"),
                total_cost_cents=Sum("cost_cents"),
                call_count=Count("id"),
            )
            .order_by("date")
        )

        # 总计
        totals = qs.aggregate(
            total_tokens=Sum("total_tokens"),
            total_cost_cents=Sum("cost_cents"),
            total_calls=Count("id"),
        )

        return {
            "period_days": days,
            "totals": {
                "total_tokens": totals["total_tokens"] or 0,
                "total_cost_cents": totals["total_cost_cents"] or 0,
                "total_calls": totals["total_calls"] or 0,
                "total_cost_yuan": round((totals["total_cost_cents"] or 0) / 100, 2),
            },
            "by_role": by_role[:20],
            "by_day": [
                {
                    "date": str(item["date"]),
                    "total_tokens": item["total_tokens"] or 0,
                    "total_cost_yuan": round((item["total_cost_cents"] or 0) / 100, 2),
                    "call_count": item["call_count"],
                }
                for item in by_day
            ],
        }


class DramaQualityService:
    """质量评估服务 — 扣分点分析 + 分集评估 + 建议应用。"""

    # 8维度定义（中文，含权重和评分标准）
    DIMENSIONS = [
        {"key": "format",     "name": "格式规范", "weight": 0.15,
         "desc": "场景头/台词格式/△标记/字数达标"},
        {"key": "structure",  "name": "结构完整", "weight": 0.20,
         "desc": "六阶段覆盖/四段式/转折点密度"},
        {"key": "character",  "name": "人物塑造", "weight": 0.15,
         "desc": "人物一致性/弧光/Ghost-Lie-Flaw体现"},
        {"key": "emotion",    "name": "情绪曲线", "weight": 0.15,
         "desc": "情绪起伏/高潮深度/低谷后的回升"},
        {"key": "dialogue",   "name": "对白质量", "weight": 0.15,
         "desc": "台词占比/差异化/潜台词/AI腔检测"},
        {"key": "hooks",      "name": "钩子效果", "weight": 0.10,
         "desc": "开篇黄金30秒/集末悬念/钩子密度"},
        {"key": "dream",      "name": "梦境指标", "weight": 0.05,
         "desc": "安全感/满足感/真实感三指标"},
        {"key": "commercial", "name": "商业可行", "weight": 0.05,
         "desc": "付费卡点/平台适配/受众匹配度"},
    ]

    # 各维度的常见问题模板（不同严重级别）
    ISSUE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "format": [
            {"id": "f001", "severity": "error",   "desc": "台词使用了引号而非冒号格式",
             "suggestion": "将\"台词\"改为：角色（情绪）：台词内容"},
            {"id": "f002", "severity": "error",   "desc": "场景头格式不规范",
             "suggestion": "场景头应为：集号-镜号 时间（日/夜/晨/昏） 内/外 地点"},
            {"id": "f003", "severity": "warning", "desc": "字数偏短，未达行业标准",
             "suggestion": "首集≥900字，其他集≥700字（含中文字符统计）"},
            {"id": "f004", "severity": "warning", "desc": "字数偏长，超出行业标准",
             "suggestion": "首集≤1100字，其他集≤900字，删除无功能过渡场景"},
            {"id": "f005", "severity": "warning", "desc": "台词占比不足28%",
             "suggestion": "将△动作描述改为台词传达信息，增加角色对峙台词"},
            {"id": "f006", "severity": "info",    "desc": "场景数量超过3个",
             "suggestion": "建议合并功能相近的相邻小场景，保持3个以内"},
        ],
        "structure": [
            {"id": "s001", "severity": "error",   "desc": "缺少集末钩子（悬念收尾）",
             "suggestion": "集末需有未解决问题或新威胁，让观众想看下集"},
            {"id": "s002", "severity": "error",   "desc": "单集结构平铺，无明显转折点",
             "suggestion": "每集需有至少1个价值逆转（McKee转变）"},
            {"id": "s003", "severity": "warning", "desc": "连续3集以上情绪平台（无起伏）",
             "suggestion": "在平台区插入情感波折或信息揭示，打破疲软"},
            {"id": "s004", "severity": "warning", "desc": "主线与支线失衡",
             "suggestion": "支线比例建议不超过主线30%，避免模糊核心冲突"},
        ],
        "character": [
            {"id": "c001", "severity": "error",   "desc": "角色行为与已建立性格不一致",
             "suggestion": "检查人设文档，确保每个决策有动机支撑"},
            {"id": "c002", "severity": "warning", "desc": "主角缺乏成长弧光",
             "suggestion": "设计Ghost（前史伤口）→Lie（错误信念）→Flaw（性格缺陷）→Truth的蜕变路径"},
            {"id": "c003", "severity": "warning", "desc": "反派动机不可理解",
             "suggestion": "反派需有清晰动机，避免纯粹邪恶的扁平化"},
        ],
        "emotion": [
            {"id": "e001", "severity": "error",   "desc": "情绪高潮点强度不足（EV<7）",
             "suggestion": "加强冲突烈度，提升情感峰值，可参考钩子设计师建议"},
            {"id": "e002", "severity": "warning", "desc": "情绪低谷过深过久（ET<2超过2集）",
             "suggestion": "低谷后需有希望信号，避免观众产生绝望感而弃剧"},
        ],
        "dialogue": [
            {"id": "d001", "severity": "error",   "desc": "检测到AI腔台词（书面用语过多）",
             "suggestion": "避免：因此/然而/于是/不得不承认，改用口语化表达"},
            {"id": "d002", "severity": "warning", "desc": "多角色台词风格雷同",
             "suggestion": "每个角色需有独特语言标签：高冷/强势/腹黑/闺蜜等"},
            {"id": "d003", "severity": "warning", "desc": "台词直接说情感（缺乏外化）",
             "suggestion": "\"我感到悲伤\"→用行为/停顿/转移话题表达，不说破"},
        ],
        "hooks": [
            {"id": "h001", "severity": "error",   "desc": "开篇30秒无视觉冲击或信息抓取",
             "suggestion": "前3秒需有强视觉冲击（冲突/逆境/反差），建立观看理由"},
            {"id": "h002", "severity": "warning", "desc": "B级以上钩子密度不足",
             "suggestion": "建议每2-3集有一个A级钩子（跨集悬念），每集有B级集末钩子"},
        ],
        "dream": [
            {"id": "dr001", "severity": "error",   "desc": "安全感不足（主角道德可疑）",
             "suggestion": "主角需有明确的道德底线，观众需能\"安全投射\""},
            {"id": "dr002", "severity": "warning", "desc": "满足感密度不足（爽感<0.8个/集）",
             "suggestion": "每集至少有0.8个爽感点：打脸/逆袭/揭穿/爱意"},
        ],
        "commercial": [
            {"id": "cm001", "severity": "warning", "desc": "付费卡点设计不足",
             "suggestion": "每集设计S/A/B/C级卡点，S级建议放在第一个付费集"},
            {"id": "cm002", "severity": "info",    "desc": "平台特性适配不足",
             "suggestion": "抖音偏重前3秒视觉冲击；快手偏重情感认同；微信偏重中年情感"},
        ],
    }

    @classmethod
    def build_detailed_quality_report(
        cls,
        scores: Dict[str, float],
        episode_number: Optional[int] = None,
        word_count_result: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        构建带扣分点的质量评估报告。

        参数：
        - scores: {"format": 85, "structure": 80, ...}
        - episode_number: 集号（None=整剧）
        - word_count_result: 字数验证结果

        返回：
        {
            "overall_score": 82,
            "grade": "A",
            "dimensions": [
                {
                    "key": "format",
                    "name": "格式规范",
                    "score": 85,
                    "weight": 0.15,
                    "issues": [{"severity": "warning", "desc": "...", "suggestion": "..."}],
                    "summary": "格式基本规范，有2处轻微问题"
                }
            ],
            "all_issues": [...],  # 按严重级别排序的全部问题
            "top_suggestions": [...],  # 最重要的3条改进建议
        }
        """
        dimensions_result = []
        all_issues = []

        for dim in cls.DIMENSIONS:
            key = dim["key"]
            score = scores.get(key, 0)
            dim_issues = cls._detect_issues_from_score(key, score, word_count_result)

            dimensions_result.append({
                "key": key,
                "name": dim["name"],
                "desc": dim["desc"],
                "score": score,
                "weight": dim["weight"],
                "issues": dim_issues,
                "issue_count": {
                    "error": sum(1 for i in dim_issues if i["severity"] == "error"),
                    "warning": sum(1 for i in dim_issues if i["severity"] == "warning"),
                    "info": sum(1 for i in dim_issues if i["severity"] == "info"),
                },
                "summary": cls._build_dim_summary(dim["name"], score, dim_issues),
            })
            all_issues.extend(dim_issues)

        # 计算综合分
        overall = scores.get("overall") or sum(
            scores.get(d["key"], 0) * d["weight"] for d in cls.DIMENSIONS
        )
        overall = round(overall, 1)

        grade = "S" if overall >= 90 else "A" if overall >= 80 else "B" if overall >= 75 else "C" if overall >= 60 else "D"

        # 按严重性排序
        severity_order = {"error": 0, "warning": 1, "info": 2}
        all_issues_sorted = sorted(all_issues, key=lambda x: severity_order.get(x["severity"], 3))

        # 最重要3条建议
        top_suggestions = [
            {"dimension": i.get("dimension", ""), "suggestion": i["suggestion"], "severity": i["severity"]}
            for i in all_issues_sorted[:3]
            if i.get("severity") in ("error", "warning")
        ]

        # 格式化字数结果（整合到格式维度）
        word_count_info = None
        if word_count_result:
            word_count_info = {
                "episode": word_count_result.get("episode"),
                "total_words": word_count_result.get("word_count", {}).get("total", 0),
                "status": word_count_result.get("word_count", {}).get("status", ""),
                "dialogue_ratio": word_count_result.get("dialogue_ratio", {}).get("ratio", ""),
                "dialogue_status": word_count_result.get("dialogue_ratio", {}).get("status", ""),
            }

        return {
            "episode_number": episode_number,
            "overall_score": overall,
            "grade": grade,
            "dimensions": dimensions_result,
            "all_issues": all_issues_sorted,
            "error_count": sum(1 for i in all_issues if i["severity"] == "error"),
            "warning_count": sum(1 for i in all_issues if i["severity"] == "warning"),
            "top_suggestions": top_suggestions,
            "word_count_info": word_count_info,
            "grade_desc": cls._grade_desc(grade),
        }

    @classmethod
    def _detect_issues_from_score(
        cls,
        dimension_key: str,
        score: float,
        word_count_result: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """根据分数和字数结果推断该维度的问题列表。"""
        issues = []
        templates = cls.ISSUE_TEMPLATES.get(dimension_key, [])

        if dimension_key == "format" and word_count_result:
            wc = word_count_result.get("word_count", {})
            dlg = word_count_result.get("dialogue_ratio", {})
            sc = word_count_result.get("scene_count", {})

            if "❌偏短" in wc.get("status", ""):
                t = next((t for t in templates if t["id"] == "f003"), None)
                if t:
                    deficit = abs(wc.get("deviation", 0))
                    issues.append({**t, "dimension": "格式规范",
                                   "desc": f"字数偏短（缺{deficit}字）"})
            elif "⚠️偏长" in wc.get("status", ""):
                t = next((t for t in templates if t["id"] == "f004"), None)
                if t:
                    surplus = abs(wc.get("deviation", 0))
                    issues.append({**t, "dimension": "格式规范",
                                   "desc": f"字数偏长（多{surplus}字）"})

            if "❌台词不足" in dlg.get("status", ""):
                t = next((t for t in templates if t["id"] == "f005"), None)
                if t:
                    issues.append({**t, "dimension": "格式规范",
                                   "desc": f"台词占比不足（当前{dlg.get('ratio', '')}，需≥28%）"})

            if "⚠️场景过多" in sc.get("status", ""):
                t = next((t for t in templates if t["id"] == "f006"), None)
                if t:
                    issues.append({**t, "dimension": "格式规范"})

        if score == 0:
            return issues

        # 分数越低，触发更多模板问题
        threshold = 90 if score >= 85 else 80 if score >= 70 else 60 if score >= 50 else 0
        for t in templates:
            sev = t["severity"]
            should_add = (
                (sev == "error" and score < 70) or
                (sev == "warning" and score < 80) or
                (sev == "info" and score < 90)
            )
            if should_add and not any(i["id"] == t["id"] for i in issues):
                issues.append({**t, "dimension": cls._dim_name(dimension_key)})

        return issues[:3]  # 最多返回3个问题，避免信息过载

    @classmethod
    def _dim_name(cls, key: str) -> str:
        for d in cls.DIMENSIONS:
            if d["key"] == key:
                return d["name"]
        return key

    @classmethod
    def _build_dim_summary(cls, dim_name: str, score: float, issues: List) -> str:
        error_count = sum(1 for i in issues if i["severity"] == "error")
        warn_count = sum(1 for i in issues if i["severity"] == "warning")
        if score >= 90:
            return f"{dim_name}表现优秀，无明显问题"
        if score >= 80:
            return f"{dim_name}基本良好" + (f"，{warn_count}处需优化" if warn_count else "")
        if score >= 70:
            return f"{dim_name}有提升空间" + (f"，{error_count}处须修复，{warn_count}处建议优化" if error_count else f"，{warn_count}处建议优化")
        return f"{dim_name}存在明显问题，{error_count}处须修复"

    @classmethod
    def _grade_desc(cls, grade: str) -> str:
        return {
            "S": "S级 · 商业精品，可直接交付",
            "A": "A级 · 质量优良，小幅优化后可交付",
            "B": "B级 · 达到基本标准，建议针对性优化",
            "C": "C级 · 存在明显不足，需系统性修改",
            "D": "D级 · 质量不达标，建议重新创作",
        }.get(grade, "")

    @classmethod
    def build_series_quality_summary(cls, episode_qualities: List[Dict]) -> Dict[str, Any]:
        """
        聚合所有集的质量数据，生成全剧质量概况。

        参数：episode_qualities 来自 DramaEpisodeQuality.objects.filter(drama_project=project)
        """
        if not episode_qualities:
            return {"total_episodes": 0, "evaluated_episodes": 0}

        scores_by_dim = {d["key"]: [] for d in cls.DIMENSIONS}
        episode_summaries = []

        for eq in episode_qualities:
            sc = eq.get("scores", {}) if isinstance(eq, dict) else (eq.scores or {})
            ep_num = eq.get("episode_number") if isinstance(eq, dict) else eq.episode_number
            for dim in cls.DIMENSIONS:
                v = sc.get(dim["key"])
                if v is not None:
                    scores_by_dim[dim["key"]].append(v)
            overall = sc.get("overall", 0)
            episode_summaries.append({
                "episode": ep_num,
                "overall": overall,
                "grade": "S" if overall >= 90 else "A" if overall >= 80 else "B" if overall >= 75 else "C" if overall >= 60 else "D",
            })

        avg_by_dim = {
            k: round(sum(v) / len(v), 1) if v else 0
            for k, v in scores_by_dim.items()
        }
        all_overalls = [e["overall"] for e in episode_summaries if e["overall"] > 0]
        series_overall = round(sum(all_overalls) / len(all_overalls), 1) if all_overalls else 0

        # 找出低分集
        weak_episodes = [e for e in episode_summaries if e["overall"] < 75]

        return {
            "total_episodes": len(episode_qualities),
            "series_overall_score": series_overall,
            "series_grade": "S" if series_overall >= 90 else "A" if series_overall >= 80 else "B" if series_overall >= 75 else "C" if series_overall >= 60 else "D",
            "avg_by_dimension": avg_by_dim,
            "episode_summaries": sorted(episode_summaries, key=lambda x: x["episode"]),
            "weak_episodes": weak_episodes,
            "weak_count": len(weak_episodes),
        }

    @classmethod
    def apply_suggestions_to_episode(
        cls,
        current_content: str,
        suggestions: List[Dict[str, Any]],
        agent_id: str,
    ) -> Dict[str, Any]:
        """
        将角色的修改建议应用到剧本原稿，生成新版本。

        此方法为占位实现，真实场景中需调用LLM对original_content进行
        基于suggestions的定向修改。

        返回：
        {
            "new_content": "修改后的剧本内容",
            "diff_summary": "改动摘要",
            "applied_count": 3,  # 实际应用的建议数
            "skipped_count": 1,  # 跳过的建议数
        }
        """
        applied = []
        skipped = []

        for sg in suggestions:
            if sg.get("auto_applicable", False):
                applied.append(sg)
            else:
                skipped.append(sg)

        # 生成变更摘要
        error_fixes = [s for s in applied if s.get("severity") == "error"]
        warn_fixes = [s for s in applied if s.get("severity") == "warning"]

        diff_parts = []
        if error_fixes:
            diff_parts.append(f"修复{len(error_fixes)}处错误：" + "、".join(s.get("desc", "")[:20] for s in error_fixes[:3]))
        if warn_fixes:
            diff_parts.append(f"优化{len(warn_fixes)}处警告：" + "、".join(s.get("desc", "")[:20] for s in warn_fixes[:3]))

        return {
            "new_content": current_content,  # TODO: 实际需要LLM处理
            "diff_summary": "；".join(diff_parts) if diff_parts else "无可自动应用的建议",
            "applied_count": len(applied),
            "skipped_count": len(skipped),
            "applied_suggestions": applied,
            "skipped_suggestions": skipped,
            "note": "当前为建议预览，实际修改需LLM执行。配置LLM后自动应用。",
        }
class DramaRoleRunService:
    """Drama 角色执行 — 桥接 creation.Project 与 IndependentAgentService。"""

    ACTIVE_STATUSES = (
        "pending",
        "running",
    )

    @staticmethod
    def ensure_creation_project(drama_project, core_idea: str = ""):
        """确保存在关联的 creation.Project（id = drama_project.project_id）。"""
        from apps.creation.models import Project

        defaults = {
            "user": drama_project.user,
            "theme": drama_project.genre_code,
            "core_idea": (core_idea or drama_project.title).strip() or drama_project.title,
            "episode_count": drama_project.total_episodes,
            "target_platform": drama_project.target_platform,
            "title": drama_project.title,
            "pipeline_mode": Project.MODE_WORKSPACE,
            "creation_entry": "from-scratch",
        }
        project, created = Project.objects.get_or_create(
            id=drama_project.project_id,
            defaults=defaults,
        )
        if not created:
            updates = {}
            if core_idea and not (project.core_idea or "").strip():
                updates["core_idea"] = core_idea.strip()
            if drama_project.title and not (project.title or "").strip():
                updates["title"] = drama_project.title
            if updates:
                for field, value in updates.items():
                    setattr(project, field, value)
                project.save(update_fields=list(updates.keys()) + ["updated_at"])
        return project

    @staticmethod
    def build_run_params(drama_project, creation_project) -> Dict[str, Any]:
        """从 Drama 项目字段构造 Agent 运行参数。"""
        return {
            "core_idea": (creation_project.core_idea or drama_project.title).strip(),
            "genre": drama_project.genre_code,
            "genre_hint": drama_project.genre_code,
            "episode_count": drama_project.total_episodes,
            "target_platform": drama_project.target_platform,
            "platform": drama_project.target_platform,
        }

    @classmethod
    def get_active_execution(cls, drama_project, agent_id: str):
        from apps.drama.models import DramaRoleExecution

        return (
            DramaRoleExecution.objects.filter(
                drama_project=drama_project,
                agent_id=agent_id,
                status__in=[
                    DramaRoleExecution.Status.PENDING,
                    DramaRoleExecution.Status.RUNNING,
                ],
            )
            .order_by("-created_at")
            .first()
        )

    @classmethod
    def enqueue_role_run(cls, drama_project, agent_id: str, user, params: Optional[Dict[str, Any]] = None):
        """创建执行记录并入队异步任务。"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.drama.models import DramaRoleExecution
        from apps.drama.tasks import run_drama_role
        from dj_queue.api import enqueue_on_commit

        agent = AgentDefinitionService.get_runnable(agent_id)

        existing = cls.get_active_execution(drama_project, agent_id)
        if existing:
            return existing, False

        creation_project = cls.ensure_creation_project(drama_project)
        run_params = dict(params or cls.build_run_params(drama_project, creation_project))

        with transaction.atomic():
            drama_exec = DramaRoleExecution.objects.create(
                drama_project=drama_project,
                agent_id=agent_id,
                agent_name_zh=agent.name_zh or agent.name,
                status=DramaRoleExecution.Status.RUNNING,
                input_artifacts={"params": run_params},
                started_at=timezone.now(),
            )
            enqueue_on_commit(run_drama_role, str(drama_exec.id))

        return drama_exec, True

    @classmethod
    def execute_role(cls, drama_execution_id: str, agent_run_id: str = "") -> Dict[str, Any]:
        """后台任务：调用 IndependentAgentService 并回写 DramaRoleExecution。"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.creation.agent_runtime.independent_service import IndependentAgentService
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        drama_exec = DramaRoleExecution.objects.select_related(
            "drama_project", "drama_project__user"
        ).get(id=drama_execution_id)
        drama_project = drama_exec.drama_project
        user = drama_project.user
        agent_id = drama_exec.agent_id
        run_params = (drama_exec.input_artifacts or {}).get("params") or {}

        creation_project = cls.ensure_creation_project(drama_project)

        try:
            if agent_run_id:
                run = AgentExecutionRun.objects.select_related("project").get(id=agent_run_id)
            else:
                result = IndependentAgentService.enqueue_run(
                    creation_project, user, agent_id, run_params
                )
                run = result.run
                if result.should_enqueue:
                    IndependentAgentService.execute_run(run)
                else:
                    run.refresh_from_db()

            cls.sync_from_agent_run(drama_exec, run, creation_project)
            drama_exec.refresh_from_db()
            return {
                "execution_id": str(drama_exec.id),
                "agent_id": agent_id,
                "status": drama_exec.status,
                "run_id": str(run.id),
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("[DramaRoleRun] 执行失败 execution=%s agent=%s", drama_execution_id, agent_id)
            cls._mark_failed(drama_exec, str(exc))
            raise

    @classmethod
    def sync_from_agent_run(cls, drama_exec, agent_run, creation_project) -> None:
        """将 AgentExecutionRun 结果同步到 DramaRoleExecution。"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.creation.artifact_service import get_artifact
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        agent = AgentDefinitionService.get_runnable(drama_exec.agent_id)
        output_keys = [str(k) for k in (agent.output_contract or {}).get("artifacts") or []]
        output_artifacts = {}
        for key in output_keys:
            payload = get_artifact(creation_project, key)
            if payload is not None:
                output_artifacts[key] = payload

        now = timezone.now()
        elapsed = None
        if drama_exec.started_at:
            elapsed = (now - drama_exec.started_at).total_seconds()

        if agent_run.status == AgentExecutionRun.STATUS_COMPLETED:
            drama_status = DramaRoleExecution.Status.SUCCESS
        elif agent_run.status == AgentExecutionRun.STATUS_FAILED:
            drama_status = DramaRoleExecution.Status.FAILED
        elif agent_run.status == AgentExecutionRun.STATUS_RUNNING:
            drama_status = DramaRoleExecution.Status.RUNNING
        else:
            drama_status = DramaRoleExecution.Status.FAILED

        drama_exec.status = drama_status
        drama_exec.output_artifacts = output_artifacts
        drama_exec.prompt_tokens = agent_run.prompt_tokens or 0
        drama_exec.completion_tokens = agent_run.completion_tokens or 0
        drama_exec.total_tokens = agent_run.total_tokens or 0
        run_params = (drama_exec.input_artifacts or {}).get("params") or {}
        try:
            from apps.creation.agent_runtime.agent_billing import resolve_coin_cost

            drama_exec.cost_cents = resolve_coin_cost(drama_exec.agent_id, run_params)
        except Exception:  # noqa: BLE001
            drama_exec.cost_cents = 0
        input_meta = dict(drama_exec.input_artifacts or {})
        input_meta["agent_run_id"] = str(agent_run.id)
        drama_exec.input_artifacts = input_meta
        drama_exec.llm_provider = agent_run.provider_name or ""
        drama_exec.llm_model = agent_run.model_name or ""
        drama_exec.error_message = (agent_run.error_message or "")[:2000]
        drama_exec.elapsed_seconds = elapsed
        drama_exec.finished_at = now if drama_status != DramaRoleExecution.Status.RUNNING else None
        drama_exec.save(
            update_fields=[
                "status",
                "output_artifacts",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "cost_cents",
                "input_artifacts",
                "llm_provider",
                "llm_model",
                "error_message",
                "elapsed_seconds",
                "finished_at",
            ]
        )

        if drama_status == DramaRoleExecution.Status.SUCCESS:
            cls._mark_project_role_completed(drama_exec)

    @classmethod
    def _mark_project_role_completed(cls, drama_exec) -> None:
        from apps.drama.progress_service import DramaProjectProgressService

        drama_project = drama_exec.drama_project
        completed = list(drama_project.completed_roles or [])
        if drama_exec.agent_id not in completed:
            completed.append(drama_exec.agent_id)
        drama_project.completed_roles = completed
        drama_project.total_tokens_used = (drama_project.total_tokens_used or 0) + (drama_exec.total_tokens or 0)
        drama_project.total_cost_cents = (drama_project.total_cost_cents or 0) + (drama_exec.cost_cents or 0)
        drama_project.save(
            update_fields=[
                "completed_roles",
                "total_tokens_used",
                "total_cost_cents",
                "updated_at",
            ]
        )
        DramaProjectProgressService.recompute_project_state(drama_project)

    @staticmethod
    def _mark_failed(drama_exec, message: str) -> None:
        from apps.drama.models import DramaRoleExecution

        drama_exec.status = DramaRoleExecution.Status.FAILED
        drama_exec.error_message = (message or "执行失败")[:2000]
        drama_exec.finished_at = timezone.now()
        if drama_exec.started_at:
            drama_exec.elapsed_seconds = (drama_exec.finished_at - drama_exec.started_at).total_seconds()
        drama_exec.save(
            update_fields=["status", "error_message", "finished_at", "elapsed_seconds"]
        )
