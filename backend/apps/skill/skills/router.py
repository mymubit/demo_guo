# -*- coding: utf-8 -*-
"""SkillRouter — 技能版本路由

根据 skill_id 从 AgentSkillDefinition DB 中查找合适版本：
  1. 优先返回 lifecycle_status=active 的版本（gray_weight=100）
  2. 若存在 lifecycle_status=gray 版本，按 gray_weight 概率分流
  3. 不存在任何 active/gray 版本时返回 None（调用方决定 fallback）

灰度分流算法：确定性哈希（基于 project_id + skill_id），同一项目始终路由到相同版本。
"""
from __future__ import annotations

import hashlib
import logging
from typing import Optional

from apps.skill.models import AgentSkillDefinition

logger = logging.getLogger(__name__)


class SkillRouter:
    """技能版本路由器"""

    @staticmethod
    def resolve(
        skill_id: str,
        *,
        project_id: str = "",
        version: str = "latest",
    ) -> Optional[AgentSkillDefinition]:
        """查找并返回应使用的技能版本

        Args:
            skill_id: 技能唯一标识
            project_id: 创作项目 ID，用于灰度确定性分流
            version: 指定版本号，"latest" 表示自动选择

        Returns:
            AgentSkillDefinition 实例，或 None（未找到）
        """
        if version != "latest":
            return SkillRouter._get_by_version(skill_id, version)

        candidates = list(
            AgentSkillDefinition.objects.filter(
                skill_id=skill_id,
                lifecycle_status__in=[
                    AgentSkillDefinition.LIFECYCLE_ACTIVE,
                    AgentSkillDefinition.LIFECYCLE_GRAY,
                ],
            ).order_by("-published_at", "-created_at")
        )

        if not candidates:
            logger.warning("技能 %r 无 active/gray 版本", skill_id)
            return SkillRouter._get_fallback(skill_id)

        active_versions = [c for c in candidates if c.lifecycle_status == AgentSkillDefinition.LIFECYCLE_ACTIVE]
        gray_versions   = [c for c in candidates if c.lifecycle_status == AgentSkillDefinition.LIFECYCLE_GRAY]

        if not gray_versions:
            return active_versions[0] if active_versions else None

        # 灰度分流：用确定性哈希决定走 active 还是 gray
        gray_version = gray_versions[0]
        hash_key = f"{project_id}:{skill_id}"
        hash_val  = int(hashlib.md5(hash_key.encode()).hexdigest(), 16) % 100
        if hash_val < gray_version.gray_weight:
            logger.debug("技能 %r 走灰度分流 (hash=%d, weight=%d)", skill_id, hash_val, gray_version.gray_weight)
            return gray_version

        return active_versions[0] if active_versions else gray_version

    @staticmethod
    def _get_by_version(skill_id: str, version: str) -> Optional[AgentSkillDefinition]:
        try:
            return AgentSkillDefinition.objects.get(skill_id=skill_id, version=version)
        except AgentSkillDefinition.DoesNotExist:
            logger.warning("技能 %r v%s 不存在", skill_id, version)
            return None

    @staticmethod
    def _get_fallback(skill_id: str) -> Optional[AgentSkillDefinition]:
        """最终兜底：返回任意 active 版本。"""
        return AgentSkillDefinition.objects.filter(
            skill_id=skill_id,
            lifecycle_status=AgentSkillDefinition.LIFECYCLE_ACTIVE,
        ).order_by("-updated_at").first()
