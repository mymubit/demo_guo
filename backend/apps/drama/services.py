# -*- coding: utf-8 -*-
"""Drama Skills 核心服务层。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


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

    @staticmethod
    def get_all_roles_grouped() -> List[Dict[str, Any]]:
        """
        获取36个角色，按部门分组，包含模型配置信息。

        返回格式：
        [
            {
                "dept_code": "strategy",
                "dept_name": "战略选题部",
                "dept_order": 1,
                "roles": [
                    {
                        "agent_id": "drama.market-radar",
                        "name_zh": "市场雷达",
                        "description": "...",
                        "is_fast_track": False,
                        "is_enabled": True,
                        "current_model": "GPT-4o",
                    }
                ]
            }
        ]
        """
        from apps.agent.models import AgentDefinition, AgentLlmRouteConfig
        from apps.drama.defaults import DRAMA_DEPARTMENTS, DRAMA_FAST_TRACK_ROLES

        # 获取所有drama_skills分类的agent
        agents = {
            a.agent_id: a
            for a in AgentDefinition.objects.filter(category="drama_skills").select_related()
        }

        # 获取LLM路由配置
        routes = {
            r.route_key: r
            for r in AgentLlmRouteConfig.objects.filter(
                route_key__startswith="drama."
            ).select_related("llm_provider")
        }

        result = []
        for dept in sorted(DRAMA_DEPARTMENTS, key=lambda d: d["order"]):
            dept_roles = []
            for agent_id, agent in sorted(agents.items()):
                if agent.ui_schema.get("dept") != dept["code"]:
                    continue

                route = routes.get(agent_id)
                model_name = "未配置"
                if route and route.llm_provider:
                    model_name = f"{route.llm_provider.name} / {route.model_name or '默认'}"

                dept_roles.append({
                    "agent_id": agent_id,
                    "name": agent.name,
                    "name_zh": agent.name_zh,
                    "description": agent.description,
                    "workspace_order": agent.workspace_order,
                    "is_fast_track": agent_id in DRAMA_FAST_TRACK_ROLES,
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
                    "roles": sorted(dept_roles, key=lambda r: r["workspace_order"]),
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
