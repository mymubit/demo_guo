# -*- coding: utf-8 -*-
"""Drama Skills 服务层"""
from __future__ import annotations

import logging
import re
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class DramaWordCountService:
    """字数校验服务 - 单集剧本格式校验"""

    # 字数阈值配置，参考 dramaskilltrae skill-thresholds.json
    FIRST_EPISODE_MIN = 900
    FIRST_EPISODE_MAX = 1100
    OTHER_EPISODE_MIN = 700
    OTHER_EPISODE_MAX = 900
    DIALOGUE_RATIO_MIN = 0.28
    MAX_SCENES = 3

    # 需要过滤的非剧本内容模式（AI备注、系统提示等）
    NON_SCRIPT_PATTERNS = [
        r"```.*?```",
        r"<!--.*?-->",
        r"\[AI\u5907\u6ce8\].*?\[/AI\u5907\u6ce8\]",
        r"\u3010\u7cfb\u7edf\u63d0\u793a\u3011.*?(?:\n/|$)",
        r"\u3010\u89d2\u8272\u8bf4\u660e\u3011.*?(?:\n/|$)",
        r"## \u8bf4\u660e\u6587\u6863.*?---",
    ]

    DIALOGUE_PATTERN = re.compile(
        r"^[^\n]+?[\uff08(][^?)]+[\uff09)]\uff1a(.+)$",
        re.MULTILINE,
    )

    SCENE_HEAD_PATTERN = re.compile(
        r"^\d+-\d+\s+[\u65e5\u591c]\s+[\u5185\u5916]\s+.+$",
        re.MULTILINE,
    )

    @classmethod
    def clean_non_script(cls, content: str) -> str:
        """清理非剧本内容（AI备注、代码块、注释等）"""
        cleaned = content
        for pattern in cls.NON_SCRIPT_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    @classmethod
    def count_cjk(cls, text: str) -> int:
        """统计CJK中日韩字符数量（中文为主）"""
        return sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')

    @classmethod
    def count_dialogue_cjk(cls, text: str) -> int:
        """统计对话中的CJK字数"""
        dialogues = cls.DIALOGUE_PATTERN.findall(text)
        return sum(cls.count_cjk(d) for d in dialogues)

    @classmethod
    def count_scenes(cls, text: str) -> int:
        """统计场景数量"""
        return len(cls.SCENE_HEAD_PATTERN.findall(text))

    @classmethod
    def validate_episode(cls, content: str, episode_number: int) -> Dict[str, Any]:
        """
        校验单集剧本格式合规性

        返回格式：
        {
            "episode": 1,
            "word_count": {"total": 1050, "target_range": [900, 1100], "status": "正常"},
            "dialogue_ratio": {"count": 320, "ratio": "30.5%", "target": "≥28%", "status": "正常"},
            "scene_count": {"count": 2, "target": "1-3", "status": "正常"},
            "overall": "达标",
            "recommendations": []
        }
        """
        cleaned = cls.clean_non_script(content)

        total_cjk = cls.count_cjk(cleaned)
        dialogue_cjk = cls.count_dialogue_cjk(cleaned)
        scene_count = cls.count_scenes(cleaned)

        # 字数阈值
        if episode_number == 1:
            min_words, max_words = cls.FIRST_EPISODE_MIN, cls.FIRST_EPISODE_MAX
        else:
            min_words, max_words = cls.OTHER_EPISODE_MIN, cls.OTHER_EPISODE_MAX

        # 对话占比
        dialogue_ratio = dialogue_cjk / total_cjk if total_cjk > 0 else 0

        # 合规判断
        word_ok = min_words <= total_cjk <= max_words
        dialogue_ok = dialogue_ratio >= cls.DIALOGUE_RATIO_MIN
        scene_ok = 1 <= scene_count <= cls.MAX_SCENES

        # 使用status_code和ok字段进行判断，避免依赖中文字符串匹配
        word_status_code = "normal" if word_ok else ("too_short" if total_cjk < min_words else "too_long")
        word_status = "正常" if word_ok else ("字数不足" if total_cjk < min_words else "字数过多")
        dialogue_status_code = "normal" if dialogue_ok else "too_low"
        dialogue_status = "正常" if dialogue_ok else "对话占比偏低"
        scene_status_code = "normal" if scene_ok else ("too_many" if scene_count > cls.MAX_SCENES else "too_few")
        scene_status = "正常" if scene_ok else ("场景数过多" if scene_count > cls.MAX_SCENES else "场景数过少")

        recommendations = []
        if not word_ok:
            if total_cjk < min_words:
                deficit = min_words - total_cjk
                recommendations.append(
                    f"字数不足{deficit}字，建议增加剧情细节、人物对话或心理描写，控制在{min_words}-{max_words}字"
                )
            else:
                surplus = total_cjk - max_words
                recommendations.append(
                    f"字数超出{surplus}字，建议精简冗余描写、合并重复场景，控制在{min_words}-{max_words}字"
                )

        if not dialogue_ok:
            actual_pct = f"{dialogue_ratio:.1%}"
            recommendations.append(
                f"对话占比{actual_pct}低于28%，建议增加人物互动和对话推进剧情，适当减少旁白描述"
            )

        if scene_count > cls.MAX_SCENES:
            recommendations.append(
                f"场景数量{scene_count}超过3个，建议合并场景或减少场景切换，单集控制在1-3个场景内"
            )
        elif scene_count < 1:
            recommendations.append(
                "未识别到有效场景，请按照'1-1 日 内 地点'格式标注场景"
            )

        overall_code = "pass" if (word_ok and dialogue_ok and scene_ok) else "needs_improvement"
        overall = "达标" if (word_ok and dialogue_ok and scene_ok) else "需优化"

        return {
            "episode": episode_number,
            "word_count": {
                "total": total_cjk,
                "target_range": [min_words, max_words],
                "deviation": total_cjk - min_words if total_cjk < min_words else (
                    total_cjk - max_words if total_cjk > max_words else 0
                ),
                "ok": word_ok,
                "status_code": word_status_code,
                "status": word_status,
            },
            "dialogue_ratio": {
                "dialogue_count": dialogue_cjk,
                "ratio": f"{dialogue_ratio:.1%}",
                "ratio_value": dialogue_ratio,
                "target": f"≥{cls.DIALOGUE_RATIO_MIN:.0%}",
                "ok": dialogue_ok,
                "status_code": dialogue_status_code,
                "status": dialogue_status,
            },
            "scene_count": {
                "count": scene_count,
                "target": f"1-{cls.MAX_SCENES}",
                "ok": scene_ok,
                "status_code": scene_status_code,
                "status": scene_status,
            },
            "overall_code": overall_code,
            "overall": overall,
            "recommendations": recommendations,
        }

    @classmethod
    def validate_all_episodes(cls, episodes: Dict[int, str]) -> Dict[str, Any]:
        """
        批量校验所有剧集

        参数：
        - episodes: {episode_number: content}

        返回：
        {
            "summary": {"total": 30, "pass": 28, "fail": 2, "avg_words": 835},
            "episodes": [单集结果],
            "issues": [问题汇总]
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
            if report["overall_code"] == "pass":
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
    """Drama Skills 角色查询服务"""

    # 层级标签配置
    TIER_LABELS = {
        1: {"name": "核心层", "desc": "快速通道必备角色，每个项目必须执行", "color": "blue"},
        2: {"name": "增强层", "desc": "复合增强角色，专家模式默认展示", "color": "green"},
        3: {"name": "专业层", "desc": "细分专业角色，按需手动调用", "color": "gray"},
    }

    @staticmethod
    def ensure_visible_roles() -> int:
        """确保 DB 中存在 12 个可见 drama 角色，不存在时执行 seed"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.agent.models import AgentDefinition
        from apps.drama.defaults import DRAMA_VISIBLE_ROLES

        existing = set(
            AgentDefinition.objects.filter(agent_id__in=DRAMA_VISIBLE_ROLES).values_list(
                "agent_id", flat=True
            )
        )
        missing = [agent_id for agent_id in DRAMA_VISIBLE_ROLES if agent_id not in existing]
        if not missing:
            return 0

        created = AgentDefinitionService.ensure_defaults()
        # seed_drama_skills 会补充 prompt/契约等完整配置
        return max(created, len(missing))

    @staticmethod
    def get_all_roles_grouped() -> List[Dict[str, Any]]:
        """
        获取按部门分组的12个可见角色

        角色分组规则：
        - 8个快速通道核心角色（tier=1），蓝色标签
        - 4个复合增强角色（tier=2），绿色标签；其余27个旧角色隐藏
        注意：tier2/3的旧角色不展示，但后台保留数据用于历史兼容
        """
        DramaRoleService.ensure_visible_roles()
        from apps.agent.models import AgentDefinition, AgentLlmRouteConfig
        from apps.drama.defaults import (
            DRAMA_DEPARTMENTS, DRAMA_FAST_TRACK_ROLES,
            DRAMA_ROLE_DEFAULTS, DRAMA_VISIBLE_ROLES,
        )

        tier_map = {r["agent_id"]: r.get("tier", 3) for r in DRAMA_ROLE_DEFAULTS}
        dept_map = {r["agent_id"]: r.get("dept", "") for r in DRAMA_ROLE_DEFAULTS}

        COMPOSITE_ROLES = {
            "drama.market-analyst", "drama.narrative-engineer",
            "drama.polish-master", "drama.production-pack",
        }

        # 只查询可见的12个角色
        agents = list(
            AgentDefinition.objects.filter(
                agent_id__in=DRAMA_VISIBLE_ROLES,
            ).order_by("workspace_order", "agent_id")
        )

        routes = {
            r.route_key: r
            for r in AgentLlmRouteConfig.objects.filter(
                route_key__startswith="drama."
            ).select_related("llm_provider")
        }

        result = []
        for dept in sorted(DRAMA_DEPARTMENTS, key=lambda d: d["order"]):
            dept_roles = []
            for agent in agents:
                agent_id = agent.agent_id
                # 优先使用 defaults 的 dept_map，兼容未同步到 defaults 的数据
                resolved_dept = dept_map.get(agent_id) or (
                    agent.ui_schema.get("dept") if isinstance(agent.ui_schema, dict) else None
                )
                if resolved_dept != dept["code"]:
                    continue

                route = routes.get(agent_id)
                model_name = "未配置"
                if route and route.llm_provider:
                    model_name = route.llm_provider.name
                elif route and route.display_name:
                    model_name = route.display_name

                tier = tier_map.get(agent_id, 2)

                dept_roles.append({
                    "agent_id": agent_id,
                    "name_zh": agent.name_zh,
                    "description": agent.description,
                    "workspace_order": agent.workspace_order,
                    "is_fast_track": agent_id in DRAMA_FAST_TRACK_ROLES,
                    "is_composite": agent_id in COMPOSITE_ROLES,
                    "tier": tier,
                    "tier_label": DramaRoleService.TIER_LABELS.get(tier, {}).get("name", "增强层"),
                    "tier_color": DramaRoleService.TIER_LABELS.get(tier, {}).get("color", "green"),
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
        获取Token消耗统计

        支持按用户/全局、按角色/按日期维度统计
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
            qs = qs.filter(project__user_id=user_id)

        # 使用values+annotate避免N+1查询问题
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
        # 补充avg_tokens
        for item in by_role:
            item["avg_tokens"] = (item["total_tokens"] or 0) / max(item["total_calls"], 1)

        # 按日期统计（最近30天）
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

        # 汇总
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
    """质量评估服务 - 8维度评分 + 问题检测 + 改进建议"""

    # 10个质量维度（基于 StoryForge G-Eval 框架，8个核心维度+2个商业维度）
    DIMENSIONS = [
        {"key": "format",     "name": "格式规范",   "weight": 0.10,
         "desc": "场景标注/人物台词格式/字数控制/对话占比/FER<5%"},
        {"key": "narrative",  "name": "叙事结构",   "weight": 0.15,
         "desc": "三幕式完整性/建置-对抗-结局/钩子-转折-高潮布局"},
        {"key": "conflict",   "name": "戏剧冲突",   "weight": 0.15,
         "desc": "核心冲突明确度/升级节奏/对抗强度/两难选择"},
        {"key": "character",  "name": "人物塑造", "weight": 0.10,
         "desc": "主角弧光/人物区分度/行为合理性/Ghost-Lie-Flaw设计"},
        {"key": "emotion",    "name": "情绪曲线",   "weight": 0.10,
         "desc": "情绪起伏设计/每3-5分钟情绪点/共情度/爽点"},
        {"key": "logic",      "name": "逻辑自洽", "weight": 0.10,
         "desc": "世界观/动机/因果链/人物行为/常识合理性"},
        {"key": "satisfaction","name": "爽点密度",  "weight": 0.10,
         "desc": "每集2-3个爽点/打脸逆袭/甜宠/反转/解压感"},
        {"key": "hooks",      "name": "钩子设计",   "weight": 0.10,
         "desc": "开场10秒钩子/集末cliffhanger/付费点钩子强度"},
        {"key": "paywall",    "name": "付费转化", "weight": 0.05,
         "desc": "付费卡点位置设计/断更点悬念/S级钩子配置"},
        {"key": "genre_fit",  "name": "题材适配", "weight": 0.05,
         "desc": "符合目标题材规范/元素完整度/受众匹配度"},
    ]

    # 各维度问题模板，按严重等级分级
    ISSUE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "format": [
            {"id": "f001", "severity": "error",   "desc": "场景标注格式错误",
             "suggestion": "按\"集-场 日/夜 内/外 地点\"格式标注场景"},
            {"id": "f002", "severity": "error",   "desc": "台词格式错误",
             "suggestion": "人物台词格式应为：角色名（情绪/动作）：台词"},
            {"id": "f003", "severity": "warning", "desc": "字数严重不足",
             "suggestion": "第一集建议900-1100字，其他集700-900字，增加细节描写"},
            {"id": "f004", "severity": "warning", "desc": "字数超出过多",
             "suggestion": "第一集不超过1100字，其他集不超过900字，精简冗余内容"},
            {"id": "f005", "severity": "warning", "desc": "对话占比低于28%",
             "suggestion": "增加人物对话，用对话推进剧情，减少旁白和场景描写"},
            {"id": "f006", "severity": "info",    "desc": "单集场景超过3个",
             "suggestion": "竖屏短剧建议单集1-3个场景，减少场景切换成本"},
        ],
        "structure": [
            {"id": "s001", "severity": "error",   "desc": "缺少开场钩子",
             "suggestion": "前30秒必须出现强冲突/悬念/反转，抓住观众注意力"},
            {"id": "s002", "severity": "error",   "desc": "缺少集末悬念或高潮",
             "suggestion": "参考McKee节拍表，每集结尾留钩子吸引下一集"},
            {"id": "s003", "severity": "warning", "desc": "前3分钟节奏偏慢无冲突",
             "suggestion": "加快节奏，快速进入核心冲突，减少铺垫篇幅"},
            {"id": "s004", "severity": "warning", "desc": "转折密度不足",
             "suggestion": "建议每3-5分钟一个小转折，提升观看粘性"},
        ],
        "character": [
            {"id": "c001", "severity": "error",   "desc": "主角动机不明确",
             "suggestion": "明确主角表层目标(Want)和深层需求(Need)，形成张力"},
            {"id": "c002", "severity": "warning", "desc": "人物弧光不足",
             "suggestion": "设计Ghost前史创伤→Lie错误认知→Flaw性格缺陷→Truth觉醒弧光"},
            {"id": "c003", "severity": "warning", "desc": "人物区分度低",
             "suggestion": "给每个角色独特的语言习惯、标志性动作和价值观"},
        ],
        "emotion": [
            {"id": "e001", "severity": "error",   "desc": "情绪价值不足，爽点EV<7分",
             "suggestion": "设计打脸/逆袭/甜宠/救赎等强情绪点，满足观众情感需求"},
            {"id": "e002", "severity": "warning", "desc": "情绪转折点不足，ET<2个/集",
             "suggestion": "安排至少2次情绪起伏，避免平铺直叙"},
        ],
        "dialogue": [
            {"id": "d001", "severity": "error",   "desc": "台词AI味重，过于书面化",
             "suggestion": "使用口语化表达，加入语气词、停顿、打断等真实对话元素"},
            {"id": "d002", "severity": "warning", "desc": "台词过于直白",
             "suggestion": "增加潜台词、言外之意，通过对话展现人物关系和矛盾"},
            {"id": "d003", "severity": "warning", "desc": "所有人说话风格相似",
             "suggestion": "根据\"身份+性格+处境\"设计差异化台词风格"},
        ],
        "hooks": [
            {"id": "h001", "severity": "error",   "desc": "前30秒没有出现强钩子",
             "suggestion": "开场3秒出冲突/悬念/异常，第一时间抓住观众"},
            {"id": "h002", "severity": "warning", "desc": "B故事/付费点钩子弱",
             "suggestion": "在第2-3集/第8-12集设计A故事+ B故事双线钩子，强化付费点"},
        ],
        "dream": [
            {"id": "dr001", "severity": "error",   "desc": "安全感不足，价值观有问题",
             "suggestion": "确保正义战胜邪恶，主角行为符合\"自卫/正义/保护\"原则"},
            {"id": "dr002", "severity": "warning", "desc": "爽点密度不足<0.8个/集",
             "suggestion": "每集至少0.8个爽点，打脸/甜宠/反转/逆袭交替安排"},
        ],
        "commercial": [
            {"id": "cm001", "severity": "warning", "desc": "爆款潜力不足",
             "suggestion": "参考S/A级爆款模板，强化三大差异化卖点和情绪钩子"},
            {"id": "cm002", "severity": "info",    "desc": "商业元素可加强",
             "suggestion": "考虑每3集一个小高潮、每10集一个大反转的商业节奏"},
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
        构建详细的质量评估报告

        参数：
        - scores: {"format": 85, "structure": 80, ...}
        - episode_number: 单集号，None=全剧汇总
        - word_count_result: 字数校验结果

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
                    "summary": "格式规范较好，存在2个小问题"
                }
            ],
            "all_issues": [...],  # 所有维度问题汇总
            "top_suggestions": [...],  # 优先修复的3个建议
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

        # 计算总分
        overall = scores.get("overall") or sum(
            scores.get(d["key"], 0) * d["weight"] for d in cls.DIMENSIONS
        )
        overall = round(overall, 1)

        grade = "S" if overall >= 90 else "A" if overall >= 80 else "B" if overall >= 75 else "C" if overall >= 60 else "D"

        # 按严重度排序问题
        severity_order = {"error": 0, "warning": 1, "info": 2}
        all_issues_sorted = sorted(all_issues, key=lambda x: severity_order.get(x["severity"], 3))

        # 取前3个优先建议
        top_suggestions = [
            {"dimension": i.get("dimension", ""), "suggestion": i["suggestion"], "severity": i["severity"]}
            for i in all_issues_sorted[:3]
            if i.get("severity") in ("error", "warning")
        ]

        # 补充字数统计信息（如果提供）
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
        """根据分数和字数结果检测该维度存在的问题"""
        issues = []
        templates = cls.ISSUE_TEMPLATES.get(dimension_key, [])

        if dimension_key == "format" and word_count_result:
            wc = word_count_result.get("word_count", {})
            dlg = word_count_result.get("dialogue_ratio", {})
            sc = word_count_result.get("scene_count", {})

            if wc.get("status_code") == "too_short":
                t = next((t for t in templates if t["id"] == "f003"), None)
                if t:
                    deficit = abs(wc.get("deviation", 0))
                    issues.append({**t, "dimension": "格式规范",
                                   "desc": f"字数不足{deficit}字"})
            elif wc.get("status_code") == "too_long":
                t = next((t for t in templates if t["id"] == "f004"), None)
                if t:
                    surplus = abs(wc.get("deviation", 0))
                    issues.append({**t, "dimension": "格式规范",
                                   "desc": f"字数超出{surplus}字"})

            if dlg.get("status_code") == "too_low":
                t = next((t for t in templates if t["id"] == "f005"), None)
                if t:
                    issues.append({**t, "dimension": "格式规范",
                                   "desc": f"对话占比{dlg.get('ratio', '')}低于28%"})

            if sc.get("status_code") == "too_many":
                t = next((t for t in templates if t["id"] == "f006"), None)
                if t:
                    issues.append({**t, "dimension": "格式规范"})

        if score == 0:
            return issues

        # 根据分数阈值匹配问题模板
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

        return issues[:3]  # 每个维度最多返回3个问题

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
            return f"{dim_name}表现优秀，是强项维度"
        if score >= 80:
            return f"{dim_name}良好" + (f"，有{warn_count}个小建议" if warn_count else "")
        if score >= 70:
            return f"{dim_name}基本合格" + (f"，存在{error_count}个错误和{warn_count}个警告" if error_count else f"，有{warn_count}个待改进项")
        return f"{dim_name}存在较大问题，有{error_count}个严重错误"

    @classmethod
    def _grade_desc(cls, grade: str) -> str:
        return {
            "S": "S级 · 精品标杆，可直接交付",
            "A": "A级 · 质量优秀，小幅润色即可",
            "B": "B级 · 整体合格，建议局部优化",
            "C": "C级 · 存在明显短板，需重点修改",
            "D": "D级 · 质量未达标，建议重写",
        }.get(grade, "")

    @classmethod
    def build_series_quality_summary(cls, episode_qualities: List[Dict]) -> Dict[str, Any]:
        """
        构建全剧质量汇总报告

        参数episode_qualities 来自 DramaEpisodeQuality.objects.filter(project=project)
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

        # 薄弱剧集（低于75分）
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
        应用修改建议到单集剧本（占位实现，待接入LLM）

        注意：当前为占位逻辑，实际需要调用LLM修改original_content
        根据suggestions生成新版本内容

        返回：
        {
            "new_content": "修改后的内容",
            "diff_summary": "修改摘要",
            "applied_count": 3,  # 已应用建议数
            "skipped_count": 1,  # 跳过建议数
        }
        """
        applied = []
        skipped = []

        for sg in suggestions:
            if sg.get("auto_applicable", False):
                applied.append(sg)
            else:
                skipped.append(sg)

        # 生成修改摘要
        error_fixes = [s for s in applied if s.get("severity") == "error"]
        warn_fixes = [s for s in applied if s.get("severity") == "warning"]

        diff_parts = []
        if error_fixes:
            diff_parts.append(f"修复{len(error_fixes)}个错误：" + "；".join(s.get("desc", "")[:20] for s in error_fixes[:3]))
        if warn_fixes:
            diff_parts.append(f"优化{len(warn_fixes)}个警告：" + "；".join(s.get("desc", "")[:20] for s in warn_fixes[:3]))

        return {
            "new_content": current_content,  # TODO: 接入LLM修改
            "diff_summary": "；".join(diff_parts) if diff_parts else "无自动可应用修改",
            "applied_count": len(applied),
            "skipped_count": len(skipped),
            "applied_suggestions": applied,
            "skipped_suggestions": skipped,
            "note": "当前为占位逻辑，实际修改需要调用LLM生成新版本内容",
        }
class DramaRoleRunService:
    """Drama 角色执行服务 - 对接 creation.Project 和 IndependentAgentService"""

    ACTIVE_STATUSES = (
        "pending",
        "running",
    )


    @staticmethod
    def build_run_params(project) -> Dict[str, Any]:
        """从 Project 构建 Agent 运行参数"""
        return {
            "core_idea": (project.core_idea or project.title or project.theme).strip(),
            "genre": project.theme,
            "genre_hint": project.theme,
            "episode_count": project.episode_count,
            "target_platform": project.target_platform,
            "platform": project.target_platform,
        }

    @classmethod
    def get_active_execution(cls, project, agent_id: str):
        from apps.drama.models import DramaRoleExecution

        return (
            DramaRoleExecution.objects.filter(
                project=project,
                agent_id=agent_id,
                status__in=[
                    DramaRoleExecution.Status.PENDING,
                    DramaRoleExecution.Status.RUNNING,
                ],
            )
            .order_by("-created_at")
            .first()
        )

    STALE_ACTIVE_MINUTES = 15

    @classmethod
    def fail_stale_active_executions(cls, project, *, stale_minutes: int | None = None) -> int:
        """将超时卡住的 Agent/Drama 执行标记为失败，防止死锁"""
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        minutes = stale_minutes if stale_minutes is not None else cls.STALE_ACTIVE_MINUTES
        threshold = timezone.now() - timedelta(minutes=minutes)
        stale_msg = "执行超时（15分钟无响应），已自动标记为失败"

        agent_fixed = AgentExecutionRun.objects.filter(
            project=project,
            status=AgentExecutionRun.STATUS_RUNNING,
            started_at__lt=threshold,
        ).update(
            status=AgentExecutionRun.STATUS_FAILED,
            error_message=stale_msg,
            finished_at=timezone.now(),
        )

        drama_stale_q = Q(started_at__lt=threshold) | Q(
            started_at__isnull=True,
            created_at__lt=threshold,
        )
        drama_fixed = DramaRoleExecution.objects.filter(
            project=project,
            status__in=[
                DramaRoleExecution.Status.PENDING,
                DramaRoleExecution.Status.RUNNING,
            ],
        ).filter(drama_stale_q).update(
            status=DramaRoleExecution.Status.FAILED,
            error_message=stale_msg,
            finished_at=timezone.now(),
        )

        synced = cls.reconcile_stale_executions(project)
        return agent_fixed + drama_fixed + synced

    @classmethod
    def reconcile_stale_executions(cls, project) -> int:
        """将 Agent 已完成但 Drama 仍显示 pending/running 的执行状态同步"""
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        stale_qs = DramaRoleExecution.objects.filter(
            project=project,
            status__in=[
                DramaRoleExecution.Status.PENDING,
                DramaRoleExecution.Status.RUNNING,
            ],
        )
        fixed = 0
        terminal = {
            AgentExecutionRun.STATUS_COMPLETED,
            AgentExecutionRun.STATUS_FAILED,
            AgentExecutionRun.STATUS_PARTIAL,
        }
        for drama_exec in stale_qs:
            meta = drama_exec.input_artifacts or {}
            agent_run_id = meta.get("agent_run_id")
            run = None
            if agent_run_id:
                run = AgentExecutionRun.objects.filter(id=agent_run_id).first()
            if not run:
                run = (
                    AgentExecutionRun.objects.filter(
                        project=project,
                        agent_id=drama_exec.agent_id,
                        started_at__gte=drama_exec.created_at,
                    )
                    .order_by("-started_at")
                    .first()
                )
            if not run or run.status not in terminal:
                continue
            cls.sync_from_agent_run(drama_exec, run, project)
            fixed += 1
        return fixed

    @classmethod
    def enqueue_role_run(cls, project, agent_id: str, user, params: Optional[Dict[str, Any]] = None):
        """入队角色执行任务（DEBUG同步模式，worker异步模式）"""
        from django.conf import settings

        from apps.agent.definition_service import AgentDefinitionService
        from apps.drama.models import DramaRoleExecution

        agent = AgentDefinitionService.get_runnable(agent_id)

        existing = cls.get_active_execution(project, agent_id)
        if existing:
            return existing, False

        run_params = dict(params or cls.build_run_params(project))
        execution_id = ""

        def _dispatch_execution() -> None:
            if getattr(settings, "DRAMA_ROLE_RUN_SYNC", settings.DEBUG):
                try:
                    cls.execute_role(execution_id)
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "[DramaRoleRun] sync execute failed execution=%s agent=%s",
                        execution_id,
                        agent_id,
                    )
                return
            from apps.drama.tasks import run_drama_role
            from dj_queue.api import enqueue_on_commit

            enqueue_on_commit(run_drama_role, execution_id)

        with transaction.atomic():
            drama_exec = DramaRoleExecution.objects.create(
                project=project,
                agent_id=agent_id,
                agent_name_zh=agent.name_zh or agent.name,
                status=DramaRoleExecution.Status.RUNNING,
                input_artifacts={"params": run_params},
                started_at=timezone.now(),
            )
            execution_id = str(drama_exec.id)
            transaction.on_commit(_dispatch_execution)

        drama_exec.refresh_from_db()
        return drama_exec, True

    @classmethod
    def execute_role(cls, drama_execution_id: str, agent_run_id: str = "") -> Dict[str, Any]:
        """执行角色任务，对接 IndependentAgentService 并更新 DramaRoleExecution"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.creation.agent_runtime.independent_service import IndependentAgentService
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        drama_exec = DramaRoleExecution.objects.select_related(
            "project", "project__user"
        ).get(id=drama_execution_id)
        project = drama_exec.project
        user = project.user
        agent_id = drama_exec.agent_id
        run_params = (drama_exec.input_artifacts or {}).get("params") or {}


        try:
            if agent_run_id:
                run = AgentExecutionRun.objects.select_related("project").get(id=agent_run_id)
            else:
                result = IndependentAgentService.enqueue_run(
                    project, user, agent_id, run_params
                )
                run = result.run
                if result.should_enqueue:
                    IndependentAgentService.execute_run(run)
                else:
                    run.refresh_from_db()

            cls.sync_from_agent_run(drama_exec, run, project)
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
    def sync_from_agent_run(cls, drama_exec, agent_run, project) -> None:
        """将 AgentExecutionRun 状态同步到 DramaRoleExecution"""
        from apps.agent.definition_service import AgentDefinitionService
        from apps.creation.artifact_service import get_artifact
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        agent = AgentDefinitionService.get_runnable(drama_exec.agent_id)
        output_keys = [str(k) for k in (agent.output_contract or {}).get("artifacts") or []]
        output_artifacts = {}
        for key in output_keys:
            payload = get_artifact(project, key)
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

        with transaction.atomic():
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
        from apps.drama.progress_service import DramaProgressService

        project = drama_exec.project
        completed = list(project.completed_roles or [])
        if drama_exec.agent_id not in completed:
            completed.append(drama_exec.agent_id)
        project.completed_roles = completed
        project.total_tokens_used = (project.total_tokens_used or 0) + (drama_exec.total_tokens or 0)
        project.total_cost_cents = (project.total_cost_cents or 0) + (drama_exec.cost_cents or 0)
        project.save(
            update_fields=[
                "completed_roles",
                "total_tokens_used",
                "total_cost_cents",
                "updated_at",
            ]
        )
        DramaProgressService.recompute_project_state(project)

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
