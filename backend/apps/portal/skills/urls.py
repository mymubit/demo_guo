# -*- coding: utf-8 -*-
"""portal skills 路由。

挂载于 /api/（通过 portal/urls.py include）后：
  GET /api/skills/<skill_id>/definition/
  GET /api/configs/<config_key>/
"""
from django.urls import path

from .views import AgentSkillDefinitionView, SkillConfigEntryView

urlpatterns = [
    path("<str:skill_id>/definition/", AgentSkillDefinitionView.as_view(), name="portal-skill-definition"),
]

config_urlpatterns = [
    path("<str:config_key>/", SkillConfigEntryView.as_view(), name="portal-skill-config"),
]
