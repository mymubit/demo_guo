# -*- coding: utf-8 -*-
"""前台公开 API：Cursor Agent 获取技能定义与配置。

需登录读取，避免核心技能规则与配置被匿名爬取。

GET /api/skills/<skill_id>/definition/
  → { skill_id, name, version, category, content(markdown), updated_at }

GET /api/configs/<config_key>/
  → { config_key, edition, version, content(json), updated_at }
"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.skill.models import AgentSkillDefinition, SkillConfigEntry
from apps.skill.skills.router import SkillRouter
from apps.console.responses import api_fail, api_ok


class AgentSkillDefinitionView(APIView):
    """返回指定 skill_id 的最新激活技能定义（Markdown 全文）。

    Cursor Agent 在读到 SKILL.md frontmatter 中 db_managed: true 时调用此接口。
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, skill_id: str = ""):
        obj = SkillRouter.resolve(skill_id)
        if not obj:
            return api_fail(f"技能 {skill_id!r} 不存在或已停用", code=404)

        return api_ok({
            "skill_id": obj.skill_id,
            "name": obj.name,
            "version": obj.version,
            "skill_layer": obj.skill_layer,
            "lifecycle_status": obj.lifecycle_status,
            "content": obj.content,
            "updated_at": obj.updated_at.isoformat(),
        })


class SkillConfigEntryView(APIView):
    """返回指定 config_key 的配置 JSON（如 skill-thresholds / qdn-emotion-engine）。

    Cursor Agent 调用此接口获取最新阈值与规则配置。
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, config_key: str = ""):
        try:
            obj = SkillConfigEntry.objects.get(config_key=config_key)
        except SkillConfigEntry.DoesNotExist:
            return api_fail(f"配置项 {config_key!r} 不存在", code=404)

        return api_ok({
            "config_key": obj.config_key,
            "edition": obj.edition,
            "version": obj.version,
            "content": obj.content,
            "updated_at": obj.updated_at.isoformat(),
        })
