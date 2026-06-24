# -*- coding: utf-8 -*-
"""Drama Skills ??????"""
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
    """?????? ? ??????????"""

    # ????????? dramaskilltrae skill-thresholds.json?
    FIRST_EPISODE_MIN = 900
    FIRST_EPISODE_MAX = 1100
    OTHER_EPISODE_MIN = 700
    OTHER_EPISODE_MAX = 900
    DIALOGUE_RATIO_MIN = 0.28
    MAX_SCENES = 3

    # ???????????AI????????
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
        """????????????????"""
        cleaned = content
        for pattern in cls.NON_SCRIPT_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    @classmethod
    def count_cjk(cls, text: str) -> int:
        """??CJK????????????"""
        return sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')

    @classmethod
    def count_dialogue_cjk(cls, text: str) -> int:
        """???????CJK?????"""
        dialogues = cls.DIALOGUE_PATTERN.findall(text)
        return sum(cls.count_cjk(d) for d in dialogues)

    @classmethod
    def count_scenes(cls, text: str) -> int:
        """???????"""
        return len(cls.SCENE_HEAD_PATTERN.findall(text))

    @classmethod
    def validate_episode(cls, content: str, episode_number: int) -> Dict[str, Any]:
        """
        ???????????

        ?????
        {
            "episode": 1,
            "word_count": {"total": 1050, "target_range": [900, 1100], "status": "???"},
            "dialogue_ratio": {"count": 320, "ratio": "30.5%", "target": "?28%", "status": "???"},
            "scene_count": {"count": 2, "target": "1-3", "status": "???"},
            "overall": "??",
            "recommendations": []
        }
        """
        cleaned = cls.clean_non_script(content)

        total_cjk = cls.count_cjk(cleaned)
        dialogue_cjk = cls.count_dialogue_cjk(cleaned)
        scene_count = cls.count_scenes(cleaned)

        # ????
        if episode_number == 1:
            min_words, max_words = cls.FIRST_EPISODE_MIN, cls.FIRST_EPISODE_MAX
        else:
            min_words, max_words = cls.OTHER_EPISODE_MIN, cls.OTHER_EPISODE_MAX

        # ????
        dialogue_ratio = dialogue_cjk / total_cjk if total_cjk > 0 else 0

        # ??
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
        ???????????

        ???
        - episodes: {episode_number: content}

        ???
        {
            "summary": {"total": 30, "pass": 28, "fail": 2, "avg_words": 835},
            "episodes": [????],
            "issues": [???????]
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
    """Drama Skills ???????"""

    # ????????????????
    TIER_LABELS = {
        1: {"name": "????", "desc": "?????????????", "color": "blue"},
        2: {"name": "????", "desc": "?????????????", "color": "green"},
        3: {"name": "????", "desc": "??????????????", "color": "gray"},
    }

    @staticmethod
    def ensure_visible_roles() -> int:
        """?? DB ???? 12 ??? drama ?????????????? seed??"""
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
        # seed_drama_skills ????? prompt/?????????????
        return max(created, len(missing))

    @staticmethod
    def get_all_roles_grouped() -> List[Dict[str, Any]]:
        """
        ???????12????????

        ???????
        - 8????????tier=1??????
        - 4?????????tier=2??????27??????
        ????tier2/3??????????????????
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

        # ??????12???
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
                # ?? defaults ? dept_map ?????????? defaults ??
                resolved_dept = dept_map.get(agent_id) or (
                    agent.ui_schema.get("dept") if isinstance(agent.ui_schema, dict) else None
                )
                if resolved_dept != dept["code"]:
                    continue

                route = routes.get(agent_id)
                model_name = "???"
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
                    "tier_label": DramaRoleService.TIER_LABELS.get(tier, {}).get("name", "????"),
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
        ??Token?????

        ?????/??/??????????
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

        # ??????????values?annotate??????????
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
        # ????avg_tokens
        for item in by_role:
            item["avg_tokens"] = (item["total_tokens"] or 0) / max(item["total_calls"], 1)

        # ???????30??
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

        # ??
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
    """?????? ? ????? + ???? + ?????"""

    # 10???????? StoryForge G-Eval ????8????????+??????
    DIMENSIONS = [
        {"key": "format",     "name": "????",   "weight": 0.10,
         "desc": "???/????/???/????/?????FER<5%"},
        {"key": "narrative",  "name": "????",   "weight": 0.15,
         "desc": "???????/???/????/??-??-????"},
        {"key": "conflict",   "name": "????",   "weight": 0.15,
         "desc": "????????/????/????/????"},
        {"key": "character",  "name": "?????", "weight": 0.10,
         "desc": "?????/??????/??????/Ghost-Lie-Flaw??"},
        {"key": "emotion",    "name": "????",   "weight": 0.10,
         "desc": "??????/??3-5?????/????/??"},
        {"key": "logic",      "name": "?????", "weight": 0.10,
         "desc": "???/??/????/?????/???????"},
        {"key": "satisfaction","name": "????",  "weight": 0.10,
         "desc": "??2-3???/???????/??/??/???"},
        {"key": "hooks",      "name": "????",   "weight": 0.10,
         "desc": "??10???/??cliffhanger??/????????"},
        {"key": "paywall",    "name": "?????", "weight": 0.05,
         "desc": "??????????/???????/S?????"},
        {"key": "genre_fit",  "name": "?????", "weight": 0.05,
         "desc": "??????????/??????/??????"},
    ]

    # ??????????????????
    ISSUE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "format": [
            {"id": "f001", "severity": "error",   "desc": "?????????????",
             "suggestion": "?\"??\"??????????????"},
            {"id": "f002", "severity": "error",   "desc": "????????",
             "suggestion": "????????-?? ????/?/?/?? ?/? ??"},
            {"id": "f003", "severity": "warning", "desc": "???????????",
             "suggestion": "???900??????700??????????"},
            {"id": "f004", "severity": "warning", "desc": "???????????",
             "suggestion": "???1100??????900???????????"},
            {"id": "f005", "severity": "warning", "desc": "??????28%",
             "suggestion": "???????????????????????"},
            {"id": "f006", "severity": "info",    "desc": "??????3?",
             "suggestion": "?????????????????3???"},
        ],
        "structure": [
            {"id": "s001", "severity": "error",   "desc": "????????????",
             "suggestion": "?????????????????????"},
            {"id": "s002", "severity": "error",   "desc": "?????????????",
             "suggestion": "??????1??????McKee???"},
            {"id": "s003", "severity": "warning", "desc": "??3????????????",
             "suggestion": "????????????????????"},
            {"id": "s004", "severity": "warning", "desc": "???????",
             "suggestion": "???????????30%?????????"},
        ],
        "character": [
            {"id": "c001", "severity": "error",   "desc": "?????????????",
             "suggestion": "??????????????????"},
            {"id": "c002", "severity": "warning", "desc": "????????",
             "suggestion": "??Ghost???????Lie???????Flaw???????Truth?????"},
            {"id": "c003", "severity": "warning", "desc": "????????",
             "suggestion": "???????????????????"},
        ],
        "emotion": [
            {"id": "e001", "severity": "error",   "desc": "??????????EV<7?",
             "suggestion": "????????????????????????"},
            {"id": "e002", "severity": "warning", "desc": "?????????ET<2??2??",
             "suggestion": "??????????????????????"},
        ],
        "dialogue": [
            {"id": "d001", "severity": "error",   "desc": "???AI???????????",
             "suggestion": "?????/??/??/?????????????"},
            {"id": "d002", "severity": "warning", "desc": "?????????",
             "suggestion": "???????????????/??/??/???"},
            {"id": "d003", "severity": "warning", "desc": "?????????????",
             "suggestion": "\"?????\"????/??/??????????"},
        ],
        "hooks": [
            {"id": "h001", "severity": "error",   "desc": "??30???????????",
             "suggestion": "?3???????????/??/??????????"},
            {"id": "h002", "severity": "warning", "desc": "B?????????",
             "suggestion": "???2-3????A?????????????B?????"},
        ],
        "dream": [
            {"id": "dr001", "severity": "error",   "desc": "?????????????",
             "suggestion": "????????????????\"????\""},
            {"id": "dr002", "severity": "warning", "desc": "??????????<0.8?/??",
             "suggestion": "?????0.8???????/??/??/??"},
        ],
        "commercial": [
            {"id": "cm001", "severity": "warning", "desc": "????????",
             "suggestion": "????S/A/B/C????S???????????"},
            {"id": "cm002", "severity": "info",    "desc": "????????",
             "suggestion": "?????3???????????????????????"},
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
        ??????????????

        ???
        - scores: {"format": 85, "structure": 80, ...}
        - episode_number: ???None=???
        - word_count_result: ??????

        ???
        {
            "overall_score": 82,
            "grade": "A",
            "dimensions": [
                {
                    "key": "format",
                    "name": "????",
                    "score": 85,
                    "weight": 0.15,
                    "issues": [{"severity": "warning", "desc": "...", "suggestion": "..."}],
                    "summary": "????????2?????"
                }
            ],
            "all_issues": [...],  # ????????????
            "top_suggestions": [...],  # ????3?????
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

        # ?????
        overall = scores.get("overall") or sum(
            scores.get(d["key"], 0) * d["weight"] for d in cls.DIMENSIONS
        )
        overall = round(overall, 1)

        grade = "S" if overall >= 90 else "A" if overall >= 80 else "B" if overall >= 75 else "C" if overall >= 60 else "D"

        # ??????
        severity_order = {"error": 0, "warning": 1, "info": 2}
        all_issues_sorted = sorted(all_issues, key=lambda x: severity_order.get(x["severity"], 3))

        # ???3???
        top_suggestions = [
            {"dimension": i.get("dimension", ""), "suggestion": i["suggestion"], "severity": i["severity"]}
            for i in all_issues_sorted[:3]
            if i.get("severity") in ("error", "warning")
        ]

        # ????????????????
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
        """????????????????????"""
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

        # ?????????????
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

        return issues[:3]  # ????3??????????

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
            return f"{dim_name}??????????"
        if score >= 80:
            return f"{dim_name}????" + (f"?{warn_count}????" if warn_count else "")
        if score >= 70:
            return f"{dim_name}?????" + (f"?{error_count}?????{warn_count}?????" if error_count else f"?{warn_count}?????")
        return f"{dim_name}???????{error_count}????"

    @classmethod
    def _grade_desc(cls, grade: str) -> str:
        return {
            "S": "S\u7ea7 \u00b7 \u7cbe\u54c1\u6807\u6746\uff0c\u53ef\u76f4\u63a5\u4ea4\u4ed8",
            "A": "A\u7ea7 \u00b7 \u8d28\u91cf\u4f18\u79c0\uff0c\u5c0f\u5e45\u6da6\u8272\u5373\u53ef",
            "B": "B\u7ea7 \u00b7 \u6574\u4f53\u5408\u683c\uff0c\u5efa\u8bae\u5c40\u90e8\u4f18\u5316",
            "C": "C\u7ea7 \u00b7 \u5b58\u5728\u660e\u663e\u77ed\u677f\uff0c\u9700\u91cd\u70b9\u4fee\u6539",
            "D": "D\u7ea7 \u00b7 \u8d28\u91cf\u672a\u8fbe\u6807\uff0c\u5efa\u8bae\u91cd\u5199",
        }.get(grade, "")

    @classmethod
    def build_series_quality_summary(cls, episode_qualities: List[Dict]) -> Dict[str, Any]:
        """
        ????????????????????

        ???episode_qualities ?? DramaEpisodeQuality.objects.filter(project=project)
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

        # ?????
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
        ??????????????????????

        ?????????????????LLM?original_content??
        ??suggestions??????

        ???
        {
            "new_content": "????????",
            "diff_summary": "????",
            "applied_count": 3,  # ????????
            "skipped_count": 1,  # ??????
        }
        """
        applied = []
        skipped = []

        for sg in suggestions:
            if sg.get("auto_applicable", False):
                applied.append(sg)
            else:
                skipped.append(sg)

        # ??????
        error_fixes = [s for s in applied if s.get("severity") == "error"]
        warn_fixes = [s for s in applied if s.get("severity") == "warning"]

        diff_parts = []
        if error_fixes:
            diff_parts.append(f"??{len(error_fixes)}????" + "?".join(s.get("desc", "")[:20] for s in error_fixes[:3]))
        if warn_fixes:
            diff_parts.append(f"??{len(warn_fixes)}????" + "?".join(s.get("desc", "")[:20] for s in warn_fixes[:3]))

        return {
            "new_content": current_content,  # TODO: ????LLM??
            "diff_summary": "?".join(diff_parts) if diff_parts else "?????????",
            "applied_count": len(applied),
            "skipped_count": len(skipped),
            "applied_suggestions": applied,
            "skipped_suggestions": skipped,
            "note": "?????????????LLM?????LLM??????",
        }
class DramaRoleRunService:
    """Drama ???? ? ?? creation.Project ? IndependentAgentService?"""

    ACTIVE_STATUSES = (
        "pending",
        "running",
    )


    @staticmethod
    def build_run_params(project) -> Dict[str, Any]:
        """? Project ???? Agent ?????"""
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
        """???????? Agent/Drama ??????????????"""
        from apps.creation.models import AgentExecutionRun
        from apps.drama.models import DramaRoleExecution

        minutes = stale_minutes if stale_minutes is not None else cls.STALE_ACTIVE_MINUTES
        threshold = timezone.now() - timedelta(minutes=minutes)
        stale_msg = "??????????? running ?"

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
        """Agent ???? Drama ? pending/running ?????????"""
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
        """??????????????DEBUG ?? worker ??????"""
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
        """??????? IndependentAgentService ??? DramaRoleExecution?"""
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
            logger.exception("[DramaRoleRun] ???? execution=%s agent=%s", drama_execution_id, agent_id)
            cls._mark_failed(drama_exec, str(exc))
            raise

    @classmethod
    def sync_from_agent_run(cls, drama_exec, agent_run, project) -> None:
        """? AgentExecutionRun ????? DramaRoleExecution?"""
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
        drama_exec.error_message = (message or "????")[:2000]
        drama_exec.finished_at = timezone.now()
        if drama_exec.started_at:
            drama_exec.elapsed_seconds = (drama_exec.finished_at - drama_exec.started_at).total_seconds()
        drama_exec.save(
            update_fields=["status", "error_message", "finished_at", "elapsed_seconds"]
        )
