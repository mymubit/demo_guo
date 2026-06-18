# -*- coding: utf-8 -*-
"""
规则进化服务层。

AI 规则进化引擎：
1. 分析过去 N 天低评分项目（overall_score < 70），提取共性缺陷
2. 根据缺陷模式生成规则修改提案
3. 支持人工审批和应用提案
"""
from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.db.models import Avg
from django.utils import timezone

logger = logging.getLogger(__name__)


class RuleEvolutionService:
    """AI 规则进化引擎"""

    def analyze_low_score_projects(
        self,
        days: int = 7,
        min_projects: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        分析过去 N 天低评分项目（overall_score < 70），提取共性缺陷。

        参数：
        - days: 分析过去多少天的项目（默认 7 天）
        - min_projects: 最少需要多少低分项目才触发分析（默认 10 个）

        返回缺陷模式列表：
        [
            {
                "pattern": "人物塑造分数持续偏低",
                "affected_projects": ["uuid1", "uuid2", ...],
                "suggestion": "建议在 Tier2 品类规范中增加人物背景深度要求",
            },
            ...
        ]
        """
        from apps.creation.models import Project, ScriptQualityDefect

        cutoff_date = timezone.now() - timedelta(days=days)

        # 获取过去 N 天内有评分的低分项目
        low_score_projects = Project.objects.filter(
            overall_score__isnull=False,
            overall_score__lt=70,
            updated_at__gte=cutoff_date,
        ).exclude(status=Project.STATUS_FAILED)

        project_count = low_score_projects.count()
        if project_count < min_projects:
            logger.info(
                "[RuleEvolution] 低分项目数量不足，跳过分析 days=%s count=%s min=%s",
                days, project_count, min_projects,
            )
            return []

        # 获取这些项目的缺陷记录
        defect_records = ScriptQualityDefect.objects.filter(
            project__in=low_score_projects,
        ).select_related("project")

        # 按缺陷维度分组统计
        dimension_stats: Dict[str, Dict[str, Any]] = {}
        project_defects: Dict[str, List[str]] = {}

        for record in defect_records:
            project_id = str(record.project_id)
            dimension = record.dimension or "unknown"

            if project_id not in project_defects:
                project_defects[project_id] = []
            project_defects[project_id].append(dimension)

            if dimension not in dimension_stats:
                dimension_stats[dimension] = {
                    "dimension": dimension,
                    "count": 0,
                    "projects": [],
                    "avg_score": None,
                    "typical_description": "",
                }

            dimension_stats[dimension]["count"] += 1
            if record.project_id not in dimension_stats[dimension]["projects"]:
                dimension_stats[dimension]["projects"].append(record.project_id)

        # 计算各维度的平均分
        for dimension, stats in dimension_stats.items():
            project_ids = stats["projects"]
            avg_score = low_score_projects.filter(id__in=project_ids).aggregate(
                avg=Avg("overall_score")
            )["avg"]
            stats["avg_score"] = avg_score
            stats["affected_projects"] = [str(p) for p in project_ids[:10]]  # 限制数量

        # 生成缺陷模式描述
        patterns = []
        for dimension, stats in dimension_stats.items():
            if stats["count"] < 3:
                continue

            pattern_desc = self._generate_pattern_description(dimension, stats)
            suggestion = self._generate_suggestion(dimension, stats)

            patterns.append({
                "pattern": pattern_desc,
                "affected_projects": stats["affected_projects"],
                "dimension": dimension,
                "defect_count": stats["count"],
                "avg_score": round(stats["avg_score"], 1) if stats["avg_score"] else None,
                "suggestion": suggestion,
            })

        # 按缺陷数量排序
        patterns.sort(key=lambda x: x["defect_count"], reverse=True)
        return patterns

    def _generate_pattern_description(self, dimension: str, stats: Dict) -> str:
        """根据缺陷维度生成模式描述。"""
        from apps.creation.quality_dimensions import quality_dimension_label

        count = stats["count"]
        avg_score = stats["avg_score"]
        label = quality_dimension_label(dimension)
        score_str = f"{avg_score:.1f}分" if avg_score else "未知"
        return f"{label}维度持续偏低（{count}个项目，平均{score_str}）"

    def _generate_suggestion(self, dimension: str, stats: Dict) -> str:
        """根据缺陷维度生成修改建议。"""
        from apps.creation.quality_dimensions import quality_dimension_suggestion

        return quality_dimension_suggestion(dimension)

    def generate_proposal(self, defect_pattern: Dict[str, Any]) -> Optional["RuleEvolutionProposal"]:
        """
        根据缺陷模式生成规则修改提案。

        调用 LLM 分析：current_tier_rules + defect_pattern → proposed_value

        参数：
        - defect_pattern: analyze_low_score_projects 返回的缺陷模式

        返回创建的 RuleEvolutionProposal（status=pending_approval）；LLM 失败时不落库，返回 None。
        """
        from apps.creation.quality_dimensions import quality_dimension_skill_id
        from apps.skill.evolution.models import RuleEvolutionProposal

        # 提取关键信息
        dimension = defect_pattern.get("dimension", "")
        suggestion = defect_pattern.get("suggestion", "")
        affected_projects = defect_pattern.get("affected_projects", [])

        # 构造 LLM 分析 prompt
        analysis_prompt = self._build_analysis_prompt(defect_pattern)
        current_tier_rules = self._fetch_current_tier_rules(dimension)

        # 调用 LLM 生成提案
        proposed_value = self._call_llm_propose(current_tier_rules, analysis_prompt)
        if proposed_value.get("error"):
            logger.warning(
                "[RuleEvolution] LLM 提案生成失败，跳过落库 dimension=%s error=%s",
                dimension,
                proposed_value.get("error"),
            )
            return None

        # 解析 LLM 返回，确定 target_tier 和 target_scope_key
        target_tier, target_scope_key = self._parse_proposal_target(
            proposed_value, dimension
        )

        # 创建提案记录
        proposal = RuleEvolutionProposal.objects.create(
            trigger_project_id=uuid.UUID(affected_projects[0]) if affected_projects else None,
            trigger_reason=defect_pattern.get("pattern", ""),
            target_skill_id=quality_dimension_skill_id(dimension),
            target_tier=target_tier,
            target_scope_key=target_scope_key,
            current_value=current_tier_rules,
            proposed_value=proposed_value,
            change_reason=suggestion,
            status=RuleEvolutionProposal.STATUS_PENDING_APPROVAL,
            proposed_by=RuleEvolutionProposal.PROPOSED_BY_AI,
        )

        logger.info(
            "[RuleEvolution] 生成提案 proposal=%s dimension=%s",
            proposal.id, dimension,
        )
        return proposal

    def _build_analysis_prompt(self, defect_pattern: Dict) -> str:
        """构造 LLM 分析 prompt。"""
        dimension = defect_pattern.get("dimension", "unknown")
        pattern = defect_pattern.get("pattern", "")
        suggestion = defect_pattern.get("suggestion", "")
        avg_score = defect_pattern.get("avg_score")

        return f"""
## 缺陷分析任务

### 发现的共性缺陷
- 维度：{dimension}
- 模式描述：{pattern}
- 平均分：{avg_score}分
- 建议修改方向：{suggestion}

### 任务
请分析上述缺陷，提出具体的规则修改方案。
包括：
1. 需要修改的规则层级（Tier）
2. 需要修改的规则范围（题材/节点）
3. 具体的规则修改值

请以 JSON 格式返回：
{{
    "target_tier": "Tier2 或 Tier3",
    "target_scope_key": "具体的题材代码或节点ID",
    "proposed_value": {{具体的规则修改内容}},
    "change_rationale": "修改理由"
}}
"""

    def _fetch_current_tier_rules(self, dimension: str) -> Dict[str, Any]:
        """
        获取当前生效的 Tier 规则。

        从 SkillRuleConfig 表读取对应维度的当前规则。
        """
        from apps.skill.models import SkillRuleConfig

        # 尝试获取 Tier2 或 Tier3 的相关规则
        rules = SkillRuleConfig.objects.filter(
            status=SkillRuleConfig.STATUS_ACTIVE,
        )

        # 按 tier 分组
        tier2_rules = rules.filter(tier=2)
        tier3_rules = rules.filter(tier=3)

        return {
            "tier2_active_count": tier2_rules.count(),
            "tier3_active_count": tier3_rules.count(),
            "dimension": dimension,
        }

    def _call_llm_propose(self, current_rules: Dict, analysis_prompt: str) -> Dict[str, Any]:
        """
        调用 LLM 生成规则修改提案。

        复用 LlmService。
        """
        from apps.skill.llm.chat import LlmService

        system_prompt = """你是一个专业的短剧创作规则专家。
根据缺陷分析结果，提出具体的规则修改方案。
请确保提案值符合 SkillRuleConfig 的 JSON 结构规范。"""

        user_prompt = f"""
当前规则状态：
{current_rules}

{analysis_prompt}

请提出具体的规则修改值（JSON 格式）。
"""

        try:
            result = LlmService.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=4096,
                json_mode=True,
            )
            return result if isinstance(result, dict) else {}
        except Exception as exc:
            logger.warning("[RuleEvolution] LLM 提案生成失败: %s", exc)
            return {
                "proposed_value": {},
                "error": str(exc),
            }

    def _parse_proposal_target(
        self,
        proposed_value: Dict,
        dimension: str,
    ) -> tuple:
        """解析 LLM 返回，确定 target_tier 和 target_scope_key。"""
        target_tier = str(proposed_value.get("target_tier", "")).strip()
        target_scope_key = str(proposed_value.get("target_scope_key", "")).strip()

        # 规范化 tier 格式
        if "tier2" in target_tier.lower() or "tier 2" in target_tier.lower():
            target_tier = "Tier2"
        elif "tier3" in target_tier.lower() or "tier 3" in target_tier.lower():
            target_tier = "Tier3"
        elif "tier1" in target_tier.lower():
            target_tier = "Tier1"
        elif "tier4" in target_tier.lower():
            target_tier = "Tier4"
        else:
            target_tier = "Tier2"  # 默认

        return target_tier, target_scope_key

    def batch_analyze_and_propose(
        self,
        days: int = 7,
        min_projects: int = 3,
    ) -> List["RuleEvolutionProposal"]:
        """
        批量执行：分析低评分项目 + 生成提案。

        参数：
        - days: 分析过去多少天的项目（默认 7 天）

        返回生成的提案列表。
        """
        # 1. 分析低评分项目
        patterns = self.analyze_low_score_projects(days=days, min_projects=min_projects)
        if not patterns:
            logger.info("[RuleEvolution] 未发现低分共性模式，跳过提案生成")
            return []

        # 2. 为每个缺陷模式生成提案
        proposals = []
        for pattern in patterns:
            try:
                proposal = self.generate_proposal(pattern)
                if proposal is not None:
                    proposals.append(proposal)
            except Exception as exc:
                logger.warning(
                    "[RuleEvolution] 提案生成失败 pattern=%s: %s",
                    pattern.get("pattern"), exc,
                )
                continue

        logger.info(
            "[RuleEvolution] 批量提案生成完成 days=%s patterns=%s proposals=%s",
            days, len(patterns), len(proposals),
        )
        return proposals

    def approve_proposal(
        self,
        proposal_id: uuid.UUID,
        approver: "settings.AUTH_USER_MODEL",
        comment: str = "",
    ) -> None:
        """
        审批通过：更新 status + approver + approved_at。
        """
        from apps.skill.evolution.models import RuleEvolutionProposal

        try:
            proposal = RuleEvolutionProposal.objects.get(pk=proposal_id)
        except RuleEvolutionProposal.DoesNotExist:
            raise ValueError(f"提案 {proposal_id} 不存在")

        if proposal.status not in (
            RuleEvolutionProposal.STATUS_DRAFT,
            RuleEvolutionProposal.STATUS_PENDING_APPROVAL,
        ):
            raise ValueError(f"提案状态不允许审批，当前状态：{proposal.status}")

        proposal.status = RuleEvolutionProposal.STATUS_APPROVED
        proposal.approved_by = approver
        proposal.approved_at = timezone.now()
        proposal.approval_comment = comment
        proposal.save(update_fields=[
            "status", "approved_by", "approved_at", "approval_comment", "updated_at",
        ])

        logger.info(
            "[RuleEvolution] 提案审批通过 proposal=%s approver=%s",
            proposal_id, approver,
        )

    def reject_proposal(
        self,
        proposal_id: uuid.UUID,
        rejector: "settings.AUTH_USER_MODEL",
        comment: str = "",
    ) -> None:
        """
        审批拒绝：更新 status + approver + approved_at。
        """
        from apps.skill.evolution.models import RuleEvolutionProposal

        try:
            proposal = RuleEvolutionProposal.objects.get(pk=proposal_id)
        except RuleEvolutionProposal.DoesNotExist:
            raise ValueError(f"提案 {proposal_id} 不存在")

        proposal.status = RuleEvolutionProposal.STATUS_REJECTED
        proposal.approved_by = rejector
        proposal.approved_at = timezone.now()
        proposal.approval_comment = comment
        proposal.save(update_fields=[
            "status", "approved_by", "approved_at", "approval_comment", "updated_at",
        ])

        logger.info(
            "[RuleEvolution] 提案被拒绝 proposal=%s rejector=%s",
            proposal_id, rejector,
        )

    def apply_proposal(self, proposal_id: uuid.UUID) -> None:
        """
        应用提案：将 proposed_value 写入 SkillRuleConfig 表。

        应用后 status → applied，并记录 applied_at。

        如果同一 (tier, scope_type, scope_key, section) 已有生效规则，
        则将旧规则归档后写入新规则。
        """
        from apps.skill.evolution.models import RuleEvolutionProposal
        from apps.skill.models import SkillRuleConfig

        try:
            proposal = RuleEvolutionProposal.objects.get(pk=proposal_id)
        except RuleEvolutionProposal.DoesNotExist:
            raise ValueError(f"提案 {proposal_id} 不存在")

        if proposal.status != RuleEvolutionProposal.STATUS_APPROVED:
            raise ValueError(f"提案状态不允许应用，当前状态：{proposal.status}")

        # 解析 proposed_value 中可能包含的 section 信息
        section = proposal.proposed_value.get("section", "requirements")
        scope_type = "genre" if proposal.target_scope_key else "global"

        # 写入 SkillRuleConfig
        from django.db import transaction

        with transaction.atomic():
            # 归档同范围的旧规则
            tier_num = int(proposal.target_tier.replace("Tier", "")) if proposal.target_tier else 2
            SkillRuleConfig.objects.filter(
                tier=tier_num,
                scope_type=scope_type,
                scope_key=proposal.target_scope_key or "",
                section=section,
                status=SkillRuleConfig.STATUS_ACTIVE,
            ).update(status=SkillRuleConfig.STATUS_ARCHIVED)

            # 创建新规则
            SkillRuleConfig.objects.create(
                tier=tier_num,
                scope_type=scope_type,
                scope_key=proposal.target_scope_key or "",
                section=section,
                content=proposal.proposed_value.get("content", proposal.proposed_value),
                version_tag="v1.0.0",
                status=SkillRuleConfig.STATUS_ACTIVE,
                source=SkillRuleConfig.SOURCE_EVOLVE,
                note=f"来自进化提案 {proposal_id}：{proposal.change_reason}",
                approved_by=str(proposal.approved_by) if proposal.approved_by else "system",
                approved_at=proposal.approved_at,
                trigger_project_ids=([str(proposal.trigger_project_id)]
                                    if proposal.trigger_project_id else []),
            )

            # 更新提案状态
            proposal.status = RuleEvolutionProposal.STATUS_APPLIED
            proposal.applied_at = timezone.now()
            proposal.save(update_fields=["status", "applied_at", "updated_at"])

        logger.info(
            "[RuleEvolution] 提案已应用 proposal=%s tier=%s scope=%s",
            proposal_id, proposal.target_tier, proposal.target_scope_key,
        )
