# -*- coding: utf-8 -*-
"""Agent 中心 Portal API — /api/agent/"""
from django.http import JsonResponse
from django.urls import path

app_name = "agent"


def deprecated_agent_catalog(request):
    return JsonResponse(
        {
            "code": 410,
            "message": "该接口已下线，请使用 /api/creation/agents/catalog/",
            "data": None,
            "deprecated": {
                "canonical_path": "/api/creation/agents/catalog/",
            },
        },
        status=410,
    )


urlpatterns = [
    path("catalog/", deprecated_agent_catalog, name="agent-catalog"),
]
