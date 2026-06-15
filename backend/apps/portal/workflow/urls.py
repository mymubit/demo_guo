# -*- coding: utf-8 -*-
"""流程中心 Portal API — /api/workflow/"""
from django.http import JsonResponse
from django.urls import path

app_name = "workflow"


def deprecated_workflow_catalog(request):
    return JsonResponse(
        {
            "code": 410,
            "message": "该接口已下线，请使用 /api/creation/fusion/catalog/",
            "data": None,
            "deprecated": {
                "canonical_path": "/api/creation/fusion/catalog/",
            },
        },
        status=410,
    )


def deprecated_workflow_nodes(request):
    return JsonResponse(
        {
            "code": 410,
            "message": "该接口已下线，请使用 /api/creation/fusion/nodes/",
            "data": None,
            "deprecated": {
                "canonical_path": "/api/creation/fusion/nodes/",
            },
        },
        status=410,
    )


urlpatterns = [
    path("catalog/", deprecated_workflow_catalog, name="workflow-catalog"),
    path("nodes/", deprecated_workflow_nodes, name="workflow-nodes"),
]
